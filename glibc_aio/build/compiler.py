import os
import subprocess
import tempfile
import urllib.request

from glibc_aio import paths


def build(version: str, arch: str, image: str | None = None,
          prefix: str | None = None, no_docker: bool = False) -> str:
    from .toolchain import resolve_image, build_script, source_url

    if prefix is None:
        prefix = str(paths.libs_build() / version / arch)
    os.makedirs(prefix, exist_ok=True)

    if not no_docker:
        docker_image = image or resolve_image(version, arch)
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("[!] Docker not found. Falling back to host-native build.")
            no_docker = True

    if not no_docker:
        script = build_script(version, arch, "/out")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\n")
            f.write(script)
            script_path = f.name

        os.chmod(script_path, 0o755)

        try:
            subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{prefix}:/out",
                "-v", f"{script_path}:/build.sh:ro",
                docker_image,
                "/build.sh",
            ], check=True)
        finally:
            os.unlink(script_path)
    else:
        srcs_dir = str(paths.srcs())
        src_dir = os.path.join(srcs_dir, f"glibc-{version}")
        if not os.path.isdir(src_dir):
            os.makedirs(srcs_dir, exist_ok=True)
            tarball = os.path.join(srcs_dir, f"glibc-{version}.tar.gz")
            if not os.path.isfile(tarball):
                url = source_url(version)
                print(f"[*] Downloading {url}")
                urllib.request.urlretrieve(url, tarball)
            os.makedirs(src_dir, exist_ok=True)
            subprocess.run(["tar", "xf", tarball, "-C", src_dir, "--strip-components=1"], check=True)

        build_dir = os.path.join(src_dir, "build")
        os.makedirs(build_dir, exist_ok=True)

        configure_args = [
            os.path.join(src_dir, "configure"),
            f"--prefix={prefix}",
            "--disable-werror",
            "--enable-debug=yes",
        ]
        if arch == "i686":
            configure_args += [
                "--host=i686-linux-gnu", "--build=i686-linux-gnu",
                "CC=gcc -m32", "CXX=g++ -m32",
            ]

        subprocess.run(configure_args, cwd=build_dir, check=True)
        subprocess.run(["make", f"-j{os.cpu_count()}"], cwd=build_dir, check=True)
        subprocess.run(["make", "install"], cwd=build_dir, check=True)

    return prefix
