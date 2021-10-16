"""Generate the generating docker image files of pwn task all in one.
"""
import argparse
import sys
import os
import pathlib
import shutil

def info(msg:str):
    print("\033[0;32m[*] INFO\033[0m : {}".format(msg))

def warn(msg:str):
    print("\033[0;33m[#] WARN\033[0m : {}".format(msg))

def err(msg:str):
    print("\033[0;31m[-] ERROR\033[0m : {}".format(msg))
    exit(-1)

class Factory:
    def __init__(self):
        self._version = None
        self._taskname = None
        self._flagname = None
        self._td = None
        self._dd = None
        self._docker_dir = None
        self._file_dir = pathlib.Path(os.path.split(os.path.realpath(__file__))[0])
        
        #------------
        self._patchelf = False
        self._libv = None
        self._libs_dir = None
    
    def __generate_about_docker_file(self, file_content, filename):
        df = self._docker_dir / filename
        df.write_text(file_content, encoding='utf-8')
        info("Create {} successfully!".format(filename))
        return self
    
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Generate the generating docker image files of pwn task all in one.')
        parser.add_argument('version', choices=[16, 18, 20, 21], type=int,
                            help='Ubuntu version of the image, only support for ubuntu 16/28/20/21.')
        parser.add_argument('-t', "--task-dir", type=pathlib.Path, required=True, help='Directory path of storing elf binary and flag.')
        parser.add_argument('-d', "--dest-dir", type=pathlib.Path, required=True, help='Directory path of files that can generate docker image.')
        parser.add_argument('-p', "--patchelf", required=False, default=False, const=True, nargs='?', help='Use patchelf or not.')
        parser.add_argument('-l', "--libc-version", type=str, required=False, help='Libc version when use patchelf.')
        # parser.add_argument('-b', "--bits", choices=[32, 64], required=False, default=64, help='Use patchelf or not.')
        args = parser.parse_args()
        self._version = args.version
        self._td = args.task_dir
        self._dd = args.dest_dir
        self._patchelf = args.patchelf
        self._libv = args.libc_version
        
        msg = "Get args ===> ubuntu version: {}\ttask-dir: {}\tdest-dir: {}\tuse patchelf: {}".format(self._version, self._td, self._dd, self._patchelf)
        if self._patchelf:
            msg += "\tlibc version: {}".format(self._libv)
        info(msg)
        return self
    
    def check_args(self):
        if not (self._td.is_dir() and self._dd.is_dir()):
            err("Task-dir or dest-dir error, make sure task-dir and dest-dir is existing! Please check you command args.")

        for f in self._td.iterdir():
            if not f.is_file():
                continue
            if "flag" in f.name:
                self._flagname = f.name
            else:
                if self._taskname is not None:
                    err("Too many files! Please make sure that there're only two file in the task-dir, one is pwn-task elf file and another is flag.")
                self._taskname = f.name
                self._docker_dir = self._dd / f.name
        
        if self._flagname is None:
            err("Cannot get flag file name, due to no file's name contains 'flag'.")
        
        if self._patchelf:
            if self._libv is None:
                err("Please specify the version of glibc when you use patchelf.")
            if not (self._file_dir / "patchelf").is_file():
                err("Cannot find patchelf in {}".format(self._file_dir))
            self._libs_dir = self._file_dir / "libs"
            # check libc version
            count = 0
            for f in self._libs_dir.iterdir():
                if f.is_file() and ("libc-{}.so".format(self._libv) == f.name or "ld-{}.so".format(self._libv) == f.name):
                    count += 1
            if count != 2:
                err("Cannot find libc-{}.so or ld-{}.so in {}".format(self._libv, self._libv, self._libs_dir))
        info("Parse args successfully! The pwn-task elf name: {}, flag name: {}".format(self._taskname, self._flagname))
        return self
    
    def mkdirs_and_move(self):
        if self._docker_dir.exists():
            while True:
                warn("Detect {} exists! Now it will be deleted, continue? [y/n]".format(self._docker_dir))
                r = input().lower()
                if r == 'y':
                    shutil.rmtree(self._docker_dir.as_posix())
                    break
                elif r == 'n':
                    info("Stop to generate these docker image files.")
                    exit(0)
                else:
                    print("Wrong input! Input again!")

        ps = self._docker_dir / "task"
        ps.mkdir(parents=True, exist_ok=True)
        shutil.copyfile((self._td / self._taskname).as_posix(), (ps / self._taskname).as_posix())
        shutil.copyfile((self._td / self._flagname).as_posix(), (ps / self._flagname).as_posix())
        if self._patchelf:
            shutil.copyfile((self._file_dir / "patchelf").as_posix(), (self._docker_dir / "patchelf").as_posix())
            # copy libc.so and ld.so
            ps = self._docker_dir / "libs"
            ps.mkdir(parents=True, exist_ok=True)
            shutil.copyfile((self._libs_dir / "libc-{}.so".format(self._libv)).as_posix(), (ps / "libc-{}.so".format(self._libv)).as_posix())
            shutil.copyfile((self._libs_dir / "ld-{}.so".format(self._libv)).as_posix(), (ps / "ld-{}.so".format(self._libv)).as_posix())
        info("Make dir of docker and move files successfully! Dir: {}".format(ps))
        return self
    
    def generate_dockerfile(self):
        file_content = """# dockerfile for {}
FROM ubuntu:{}.04

RUN sed -i "s/http:\/\/archive.ubuntu.com/http:\/\/mirrors.tuna.tsinghua.edu.cn/g" /etc/apt/sources.list && \\
    apt-get update && apt-get -y dist-upgrade && \\
    apt-get install -y lib32z1 xinetd

RUN useradd -m ctf 

WORKDIR /home/ctf

RUN cp -R /lib* /home/ctf && \\
    cp -R /usr/lib* /home/ctf

RUN mkdir /home/ctf/dev && \\
    mknod /home/ctf/dev/null c 1 3 && \\
    mknod /home/ctf/dev/zero c 1 5 && \\
    mknod /home/ctf/dev/random c 1 8 && \\
    mknod /home/ctf/dev/urandom c 1 9 && \\
    chmod 666 /home/ctf/dev/*

RUN mkdir /home/ctf/bin && \\
    cp /bin/sh /home/ctf/bin && \\
    cp /bin/ls /home/ctf/bin && \\
    cp /bin/cat /home/ctf/bin

COPY ./ctf.xinetd /etc/xinetd.d/ctf
COPY ./start.sh /start.sh
COPY ./task/ /home/ctf/

""".format(self._taskname, self._version)
        if self._patchelf:
            file_content += """# patchelf
COPY ./libs /libs
COPY ./patchelf /usr/bin/patchelf
COPY ./libs /home/ctf/libs
RUN chmod +x /usr/bin/patchelf

"""

        file_content += """# chmod 
RUN echo "Blocked by ctf_xinetd" > /etc/banner_fail && \\
    chmod +x /start.sh && \\
    chown -R root:ctf /home/ctf && \\
    chmod -R 750 /home/ctf && \\
    chmod 740 /home/ctf/flag

CMD ["/start.sh"]

EXPOSE 9999
"""

        self.__generate_about_docker_file(file_content, "Dockerfile")
        return self
    
    def generate_dockercompose_file(self):
        file_content = """# docker-compose.yaml for {}
version: "3"
services:
  {}:
    build: .
    restart: unless-stopped
    ports:
      - "23333:9999"
""".format(self._taskname, self._taskname)
        self.__generate_about_docker_file(file_content, "docker-compose.yaml")
        return self
    
    
    def generate_ctf_xinetd(self):
        file_content = """service ctf
{{
    disable = no
    socket_type = stream
    protocol    = tcp
    wait        = no
    user        = root
    type        = UNLISTED
    port        = 9999
    bind        = 0.0.0.0
    server      = /usr/sbin/chroot
    # replace pwn to your program
    server_args = --userspec=1000:1000 /home/ctf ./{}
    banner_fail = /etc/banner_fail
    # safety options
    per_source	= 10 # the maximum instances of this service per source IP address
    rlimit_cpu	= 20 # the maximum number of CPU seconds that the service may use
    # rlimit_as  = 1024M # the Address Space resource limit for the service
    # access_times = 2:00-9:00 12:00-24:00
}}
""".format(self._taskname)
        self.__generate_about_docker_file(file_content, "ctf.xinetd")
        return self

    def generate_start_sh(self):
        file_content = """#!/bin/sh
# add you own script here

"""
        if self._patchelf:
            file_content += """# patchelf 
patchelf --set-interpreter /libs/ld-{}.so ./{}
patchelf --replace-needed libc.so.6 /libs/libc-{}.so ./{}
""".format(self._libv, self._taskname, self._libv, self._taskname)

        file_content += """# DO NOT DELETE
/etc/init.d/xinetd start;
sleep infinity;
"""
        self.__generate_about_docker_file(file_content, "start.sh")
        return self

    def generate_builup_sh(self):
        file_content = """#!/bin/sh
# build docker image for {}
docker-compose up -d 

# exec poc to validate
# python3 exp.py 127.0.0.1 23333 flag{{test_flag}} 
""".format(self._taskname)
        self.__generate_about_docker_file(file_content, "build_image.sh")
        return self


if __name__ == '__main__':
    Factory().\
    parse_args().\
    check_args().\
    mkdirs_and_move().\
    generate_dockerfile().\
    generate_dockercompose_file().\
    generate_ctf_xinetd().\
    generate_start_sh().\
    generate_builup_sh()