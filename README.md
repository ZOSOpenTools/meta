# Meta - Introducing the zopen package manager

Meta adds package management facilities to z/OS, via `zopen`. It is similar to utilities like apt, dpkg, yum, yast2, and emerge. It is written as a pure shell script to remove any prerequisites (like python/perl/bash etc).
This package manager is designed for everyday usage of the z/OS Open Tools ports within the z/OS UNIX environment or for those who wish to download the tools.

**Download** the latest zopen package manager [here](https://github.com/ZOSOpenTools/meta/releases).

## Pre-config

It is advised to have the following set on the system to ensure correct operation:

```bash
export _BPXK_AUTOCVT=ON
export _CEE_RUNOPTS="$_CEE_RUNOPTS FILETAG(AUTOCVT,AUTOTAG) POSIX(ON)"
export _TAG_REDIR_ERR=txt
export _TAG_REDIR_IN=txt
export _TAG_REDIR_OUT=txt
```

Make sure the character device `/dev/tty` is untagged or you may experience unexpected behaviour. Run `chtag -r /dev/tty` to remove any tags.

## Installation

* Download the meta pax to a suitable location (for example /tmp).
* Expand the pax using the command `pax -rvf <filename>.pax.Z`.  This will expand the pax to the current directory, listing the various included files as it does so.
* From the `meta-<ver>` directory run the following command, answering the questions appropriately:

```bash
. ./.env
zopen init
```

You can now safely remove `meta-<version>.pax.Z` and the extracted `meta-<version>` directory

## Sample usage

```bash
. ./.env # Source the .env from meta
zopen init
. <zopen_root_path>/etc/zopen-config
zopen list --installed
zopen install which
zopen list --installed
which which
zopen upgrade
zopen install git vim # install both git and vim
```

## Important usage notes

* Remote repositories utilise the suffix `port` - where required, packages should be specified **without** the suffix. For example, using `zopen install which` rather than `zopen install whichport`.

## Root filesystem install

* Selecting `'/'` as the root filesystem will allow the tools to be available system-wide for all users who configure their usage. The install needs to be done by a sysadmin [or someone with sufficient rights using the `sudo` port for example] as the installer will write files to the `/usr` tree and configuration information to /etc. There will also be a configuration file written as `/etc/zopen-config` - this can be sourced by other users.

* Removing zopen and the z/OS Open Tools once installed involves:
  * Uninstalling all installed packages; removing any copies of `zopen-config`
  * Removing the configured zopen root directory (by default `/usr/local/zopen` but is set during installation)
  * Running a command to find any final orphaned symlinks on the system, such as: `/bin/find $ZOPEN_ROOTFS -type l -exec test ! -e {} \; -print`
    where `$ZOPEN_ROOTFS` is '`/`'
    * Replace `-print` with `rm -rf` to actually remove symlinks, the example command should only list what was found.
    * Care should be taken when removing any files with sysadmin authority to prevent removing critical files!

## Basic command introduction

Most commands have extended help available using the `--help` parameter.  The following usage guidance should be sufficient to get a system running.

```bash
zopen init
```

Used to initialise a z/OS Open Tools environment. By default, this will create a `zopen` directory in your `$HOME` directory as the root filesystem (rootfs).  The rootfs holds the various packages, configuration files, and environment for z/OS Open Tools packages. Removing this directory will revert the system without a trace.  A z/OS Open Tools main configuration file is generated in `$rootfs/etc/zopen-config`. To enable the z/OS Open Tools, this will either need to be sourced after logon to the system or the following line can be added to `$HOME/.profile` (or .bash_profile or...) to automatically source the z/OS Open Tools configuration file.

```bash
[ -e "$rootfs/etc/zopen-config" ] && . $rootfs/etc/zopen-config
```

It is possible to reinitialize a system using the `re-init` option - doing so will remove the previous configuration though the rootfs can overlap the old filesystem to reuse installed and/or cached packages for example.  Initialisation on a system that has previously had a z/OS Open Tools configuration should allow some parameters to be copied across, such as Github tokens.

```bash
zopen install <package>...
```

Used to install a z/OS Open Tools package.  By default, the latest stable version is installed although options are available to install specific versions, tags or to pick from a selection [see `--help` for more].

```bash
zopen upgrade
```

Used to upgrade z/OS Open Tools packages.  Without parameters, all installed packages will be upgraded; individual packages can be specified on the command line to upgrade only those packages.  Packages can be "pinned" to prevent upgrading in case a later release is found to be broken or incompatible - creating a `.pinned` file in the package directory prevents the upgrade; removing the file allows upgrades to occur.

```bash
zopen clean [--cache] [--unused] [--dangling] [--all]
```

Used to remove resources on the system.  zopen will retain old versions of packages to allow for switching versions or quick re-installs; downloaded pax files are held in a cache while the specific version files are maintained in the directory configured during initialisation.  Using the `clean` option removes those unused resources.  In addition, zopen utilises symlinks for maintaining the appropriate file structure. Should a problem occur during package installation, removal, or version change, dangling symlinks might be present. The `--dangling` option will (slowly) analyse the rootfs and prune any dangling symlinks.

```bash
zopen alt [package] [-s]
```

Used to list versions of a package if there are multiple versions present; using the `-s` parameter allows for the active version to be changed.

```bash
zopen remove <package>...
```

Removes a package from the system, leaving the version on the system for re-use later; the `---purge` directory will also remove the versioned directory, requiring a potential download and/or an unpax to occur to re-install that version..

```bash
zopen list [--installed]
```

With no parameters, will list the available packages against the currently installed versions; more usefully, using the `--installed` parameter lists the actually locally-installed packages rather than all potential packages

```bash
zopen query --remote-search <package>
```

Searches the remote repository for the specified package, returning appropriate meta-data about the package if found.

```bash
zopen query <option>
```

Queries the local z/OS Open Tools system. See `---help` for more details.

## Migrating from zopen version <0.8.0
**Note:** The new zopen package manager is not compatible with previous versions of zopen. Migration involves creating a new directory structure for zopen tools. This is accomplished via the `zopen init` command, documented below.

### Before you migrate

* Identify the tools you have already installed. Use `zopen install --list`.
* If you plan to reuse the existing zopen root directory for installing the new tools, then make sure to back it up to a different directory.
* Follow the steps below and install each of the tools again via `zopen install`


### Useful resources

* View the z/OS Open Tools project home: https://github.com/ZOSOpenTools
* View the main Meta documentation at https://zosopentools.github.io/meta/
