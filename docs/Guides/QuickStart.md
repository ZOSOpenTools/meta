# Quick Start to z/OS Open Tools

z/OS Open Tools provides a package manager for 
installation of unsupported Open Source tools that run native on your z/OS system. 

z/OS Open Tools also provides an easy to use tool for building these same tools from 
source code on your z/OS system. 

Whether you want to _use_ the tools or also _improve_ the tools is up to you.

If you have installed a version of the zopen package manager prior to September 2023, 
please note you will need to [migrate to the new package manager](Migration.md). 

## Getting the zopen package manager

- Download the latest [meta pax](https://github.com/ZOSOpenTools/meta/releases) to your desktop, then upload to z/OS
- On z/OS, expand the pax file: `pax -rf meta-<version>.pax.Z`. 
- cd to the unpax'ed directory: `cd meta-<version>`
- Set up the PATH to the `zopen` tool: `cd meta-<version>; . ./.env`
- Initialize the `zopen tools` environment: `zopen init`
- Set up your zopen environment by sourcing the zopen-config file `. $ZOPEN_ROOTFS/etc/zopen-config`, where `$ZOPEN_ROOTFS` is the location to your zopen file system.\*
- Install tools you want with `zopen install <tool>`
- You can now safely remove `meta-<version>.pax.Z` and the `meta-<version>` directory


* **Note**: We recommend that you add the line `. $ZOPEN_ROOTFS/etc/zopen-config` to your `.profile` startup script. Alternatively, you can use `zopen init --append-to-profile` when setting up your zopen file-system.

See [The package manager](ThePackageManager.md) and [Developing Tools](developing.md) for more details.

## Getting Started Video
If you like learning through watching, check out our getting started Video:
<video height="1080" controls>
  <source src="https://github.com/ZOSOpenTools/collateral/raw/main/ZOSOpenToolsIntroV2-cropped.mp4" type="video/mp4">
</video>


## Upgrading z/OS Open Tools

z/OS Open Tools can be upgraded like so:

```
$ zopen upgrade
```

In this case, all packages including the package manager, `zopen` (via the meta package manager) will
be updated sequentially while being prompted to perform the update.
Using the option `-y` will automatically accept all prompts as
shown here:

```
$ zopen upgrade -y
```


## Upgrading a single package

Individual packages can be upgraded by specifiying the package
name.  For example upgrading just the package manager is
accomplished like so:

```
$ zopen upgrade meta -y
$ zopen init --re-init
# This assumes zopen is installed in your $HOME directory
$ . ~/zopen/etc/zopen-config
```

Note, for users of meta 0.6.x and earlier, if the upgrade fails because of a pinned message, find the 
`.pinned` file and remove it.  Afterwards `zopen upgrade meta -y` will
work.

For example:

```
$ cd ~/zopen
$ find . -name ".pinned"
./meta-0.6.2/.pinned
./usr/local/zopen/meta/meta-dt/.pinned
$ rm ./usr/local/zopen/meta/meta-dt/.pinned
# This is a version installed as part of the install process and
# can be safely removed once installed.
$ rm -rf ./meta-0.6.2/.pinned
```


