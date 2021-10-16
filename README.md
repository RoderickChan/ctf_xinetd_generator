# ctf_xinetd_generator
From <https://github.com/Eadom/ctf_xinetd>
> A repository for generating files that can generate pwn-task docker image

## Usage
```
git clone https://github.com/RoderickChan/ctf_xinetd_generator.git
cd ctf_xinetd_generator
python3 generator.py 18 --task-dir ./bin --dest-dir /tmp
```

if you want to use `patchelf`, then type:

```
python3 generator.py 18 --task-dir ./bin --dest-dir /tmp --patchelf --libc-version 2.32
```

Or just use prefix to geenrate:

```
python3 generator.py 18 -t ./bin -d /tmp -p -l 2.32
```

## Help

type `python3 generator.py -h` to get help:

```
python generator.py -h
usage: generator.py [-h] -t TASK_DIR -d DEST_DIR [-p [PATCHELF]]
                   [-l LIBC_VERSION]
                   {16,18,20,21}

Generate the generating docker image files of pwn task all in one.

positional arguments:
  {16,18,20,21}         Ubuntu version of the image, only support for ubuntu
                        16/28/20/21.

optional arguments:
  -h, --help            show this help message and exit
  -t TASK_DIR, --task-dir TASK_DIR
                        Directory path of storing elf binary and flag.
  -d DEST_DIR, --dest-dir DEST_DIR
                        Directory path of files that can generate docker
                        image.
  -p [PATCHELF], --patchelf [PATCHELF]
                        Use patchelf or not.
  -l LIBC_VERSION, --libc-version LIBC_VERSION
                        Libc version when use patchelf.
```
