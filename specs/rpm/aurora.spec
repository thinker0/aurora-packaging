#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Overridable variables;
%if %{?!AURORA_VERSION:1}0
%global AURORA_VERSION 0.9.0
%endif

%if %{?!AURORA_USER:1}0
%global AURORA_USER aurora
%endif

%if %{?!AURORA_GROUP:1}0
%global AURORA_GROUP aurora
%endif

%if %{?!GRADLE_BASEURL:1}0
%global GRADLE_BASEURL https://services.gradle.org/distributions
%endif

%if %{?!GRADLE_VERSION:1}0
%global GRADLE_VERSION 2.5
%endif

%if %{?!JAVA_VERSION:!}0
%global JAVA_VERSION 1.8.0
%endif

%if %{?!MESOS_VERSION:1}0
%global MESOS_VERSION 0.22.0
%endif

%if %{?!PEX_BINARIES:1}0
%global PEX_BINARIES aurora aurora_admin thermos thermos_executor thermos_runner thermos_observer
%endif

%if %{?!PYTHON_VERSION:1}0
%global PYTHON_VERSION 2.7
%endif


Name:          aurora
Version:       %{AURORA_VERSION}
Release:       1%{?dist}.aurora
Summary:       A Mesos framework for scheduling and executing long-running services and cron jobs.
Group:         Applications/System
License:       ASL 2.0
URL:           https://%{name}.apache.org/

Source0:       https://github.com/apache/%{name}/archive/%{version}/%{name}.tar.gz
Source1:       aurora.service
Source2:       thermos-observer.service
Source3:       aurora.init.sh
Source4:       thermos-observer.init.sh
Source5:       aurora.startup.sh
Source6:       thermos-observer.startup.sh
Source7:       aurora.sysconfig
Source8:       thermos-observer.sysconfig
Source9:       aurora.logrotate
Source10:      thermos-observer.logrotate
Source11:      clusters.json
Source12:      aurora.monit
Source13:      thermos-observer.monit

BuildRequires: apr-devel
BuildRequires: cyrus-sasl-devel
BuildRequires: gcc
BuildRequires: gcc-c++
BuildRequires: git
BuildRequires: java-%{JAVA_VERSION}-openjdk-devel
BuildRequires: krb5-devel
BuildRequires: libcurl-devel
BuildRequires: patch
%if 0%{?rhel} && 0%{?rhel} < 7
BuildRequires: python27
BuildRequires: python27-scldevel
%else
BuildRequires: python
BuildRequires: python-devel
%endif
BuildRequires: subversion-devel
BuildRequires: tar
BuildRequires: unzip
BuildRequires: wget
BuildRequires: zlib-devel

%if 0%{?rhel} && 0%{?rhel} < 7
Requires:      daemonize
%endif
Requires:      java-%{JAVA_VERSION}-openjdk
Requires:      mesos = %{MESOS_VERSION}


%description
Apache Aurora is a service scheduler that runs on top of Mesos, enabling you to schedule
long-running services that take advantage of Mesos' scalability, fault-tolerance, and
resource isolation.


%package client
Summary: A client for scheduling services against the Aurora scheduler
Group: Development/Tools

Requires: krb5-libs
%if 0%{?rhel} && 0%{?rhel} < 7
Requires: python27
%else
Requires: python
%endif

%description client
A set of command-line applications used for interacting with and administering Aurora
schedulers.


%package thermos
Summary: Mesos executor that runs and monitors tasks scheduled by the Aurora scheduler
Group: Applications/System

Requires: cyrus-sasl
%if 0%{?rhel} && 0%{?rhel} < 7
Requires: daemonize
Requires: docker-io
Requires: monit
%else
Requires: docker
%endif
Requires: mesos = %{MESOS_VERSION}
%if 0%{?rhel} && 0%{?rhel} < 7
Requires: python27
%else
Requires: python
%endif

%description thermos
Thermos a simple process management framework used for orchestrating dependent processes
within a single Mesos chroot.  It works in tandem with Aurora to ensure that tasks
scheduled by it are properly executed on Mesos slaves and provides a Web UI to monitor the
state of all running tasks.


%prep
%setup -n apache-%{name}-%{version}


%build
# Preferences SCL-installed Python 2.7 if we're building on EL6.
%if 0%{?rhel} && 0%{?rhel} < 7
export PATH=/opt/rh/python27/root/usr/bin${PATH:+:${PATH}}
export LD_LIBRARY_PATH=/opt/rh/python27/root/usr/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export MANPATH=/opt/rh/python27/root/usr/share/man:${MANPATH}
# For systemtap
export XDG_DATA_DIRS=/opt/rh/python27/root/usr/share${XDG_DATA_DIRS:+:${XDG_DATA_DIRS}}
# For pkg-config
export PKG_CONFIG_PATH=/opt/rh/python27/root/usr/lib64/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}
%endif

# Preferences Java 1.8 over any other Java version.
export PATH=/usr/lib/jvm/java-1.8.0/bin:${PATH}

# Downloads Gradle executable.
wget %{GRADLE_BASEURL}/gradle-%{GRADLE_VERSION}-bin.zip
unzip gradle-%{GRADLE_VERSION}-bin.zip

# Builds the Aurora scheduler.
./gradle-%{GRADLE_VERSION}/bin/gradle installDist

# Configures pants to use our distributed platform-specific eggs.
# This avoids building mesos to produce them.
export PANTS_CONFIG_OVERRIDE=/pants.ini

# Builds Aurora client PEX binaries.
./pants binary src/main/python/apache/aurora/client/cli:kaurora
mv dist/kaurora.pex dist/aurora.pex
./pants binary src/main/python/apache/aurora/admin:kaurora_admin
mv dist/kaurora_admin.pex dist/aurora_admin.pex

# Builds Aurora Thermos and GC executor PEX binaries.
./pants binary src/main/python/apache/aurora/executor/bin:thermos_executor
./pants binary src/main/python/apache/aurora/tools:thermos
./pants binary src/main/python/apache/thermos/bin:thermos_runner
./pants binary src/main/python/apache/aurora/tools:thermos_observer

# Packages the Thermos runner within the Thermos executor.
build-support/embed_runner_in_executor.py

%install
rm -rf $RPM_BUILD_ROOT

# Builds installation directory structure.
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_docdir}/%{name}-%{version}
mkdir -p %{buildroot}%{_prefix}/lib/%{name}
mkdir -p %{buildroot}%{_sharedstatedir}
mkdir -p %{buildroot}%{_localstatedir}/lib/%{name}
mkdir -p %{buildroot}%{_localstatedir}/log/%{name}
mkdir -p %{buildroot}%{_localstatedir}/log/thermos
mkdir -p %{buildroot}%{_localstatedir}/run/thermos
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/init.d
mkdir -p %{buildroot}%{_sysconfdir}/monit.d
mkdir -p %{buildroot}%{_sysconfdir}/systemd/system
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig

# Installs the Aurora scheduler that was just built into /usr/lib/aurora.
cp -r dist/install/aurora-scheduler/* %{buildroot}%{_prefix}/lib/%{name}

# Installs all PEX binaries.
for pex_binary in %{PEX_BINARIES}; do
  install -m 755 dist/${pex_binary}.pex %{buildroot}%{_bindir}/${pex_binary}
done

# Installs all support scripting.
%if 0%{?fedora} || 0%{?rhel} > 6
install -m 644 build-support/packaging/rpm/%{name}.service %{buildroot}%{_sysconfdir}/systemd/system/%{name}.service
install -m 644 build-support/packaging/rpm/thermos-observer.service %{buildroot}%{_sysconfdir}/systemd/system/thermos-observer.service
%else
install -m 755 build-support/packaging/rpm/%{name}.init.sh %{buildroot}%{_sysconfdir}/init.d/%{name}
install -m 755 build-support/packaging/rpm/thermos-observer.init.sh %{buildroot}%{_sysconfdir}/init.d/thermos-observer
%endif

install -m 755 build-support/packaging/rpm/%{name}.startup.sh %{buildroot}%{_bindir}/%{name}-scheduler-startup
install -m 755 build-support/packaging/rpm/thermos-observer.startup.sh %{buildroot}%{_bindir}/thermos-observer-startup

install -m 644 build-support/packaging/rpm/%{name}.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/%{name}
install -m 644 build-support/packaging/rpm/thermos-observer.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/thermos-observer

install -m 644 build-support/packaging/rpm/%{name}.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -m 644 build-support/packaging/rpm/thermos-observer.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/thermos-observer

install -m 644 build-support/packaging/rpm/clusters.json %{buildroot}%{_sysconfdir}/%{name}/clusters.json

install -m 644 %{SOURCE12} %{buildroot}%{_sysconfdir}/monit.d/aurora.conf
install -m 644 %{SOURCE13} %{buildroot}%{_sysconfdir}/monit.d/thermos-observer.conf

%pre
getent group %{AURORA_GROUP} > /dev/null || groupadd -r %{AURORA_GROUP}
getent passwd %{AURORA_USER} > /dev/null || \
    useradd -r -d %{_localstatedir}/lib/%{name} -g %{AURORA_GROUP} \
    -s /bin/bash -c "Aurora Scheduler" %{AURORA_USER}
exit 0

# Pre/post installation scripts:
%post
%if 0%{?fedora} || 0%{?rhel} > 6
%systemd_post %{name}.service
%else
/sbin/chkconfig --add %{name}
%endif

%preun
%if 0%{?fedora} || 0%{?rhel} > 6
%systemd_preun %{name}.service
%else
/sbin/service %{name} stop >/dev/null 2>&1
/sbin/chkconfig --del %{name}
%endif

%postun
%if 0%{?fedora} || 0%{?rhel} > 6
%systemd_postun_with_restart %{name}.service
%else
/sbin/service %{name} start >/dev/null 2>&1
%endif


%post thermos
%if 0%{?fedora} || 0%{?rhel} > 6
%systemd_post thermos-observer.service
%else
/sbin/chkconfig --add thermos-observer
%endif

%preun thermos
%if 0%{?fedora} || 0%{?rhel} > 6
%systemd_preun thermos-observer.service
%else
/sbin/service thermos-observer stop >/dev/null 2>&1
/sbin/chkconfig --del thermos-observer
%endif

%postun thermos
%if 0%{?fedora} || 0%{?rhel} > 6
%systemd_postun_with_restart thermos-observer.service
%else
/sbin/service thermos-observer start >/dev/null 2>&1
%endif


%files
%defattr(-,root,root,-)
%doc docs/*.md
%{_bindir}/aurora-scheduler-startup
%attr(-,%{AURORA_USER},%{AURORA_GROUP}) %{_localstatedir}/lib/%{name}
%attr(-,%{AURORA_USER},%{AURORA_GROUP}) %{_localstatedir}/log/%{name}
%{_prefix}/lib/%{name}/bin/*
%{_prefix}/lib/%{name}/etc/*
%{_prefix}/lib/%{name}/lib/*
%if 0%{?fedora} || 0%{?rhel} > 6
%{_sysconfdir}/systemd/system/%{name}.service
%else
%{_sysconfdir}/init.d/%{name}
%config(noreplace) %{_sysconfdir}/monit.d/%{name}.conf
%endif
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}


%files client
%defattr(-,root,root,-)
%{_bindir}/%{name}
%{_bindir}/%{name}_admin
%config(noreplace) %{_sysconfdir}/%{name}/clusters.json


%files thermos
%defattr(-,root,root,-)
%{_bindir}/thermos
%{_bindir}/thermos_executor
%{_bindir}/thermos_observer
%{_bindir}/thermos_runner
%{_bindir}/thermos-observer-startup
%{_localstatedir}/log/thermos
%{_localstatedir}/run/thermos
%if 0%{?fedora} || 0%{?rhel} > 6
%{_sysconfdir}/systemd/system/thermos-observer.service
%else
%{_sysconfdir}/init.d/thermos-observer
%config(noreplace) %{_sysconfdir}/monit.d/thermos-observer.conf
%endif
%config(noreplace) %{_sysconfdir}/logrotate.d/thermos-observer
%config(noreplace) %{_sysconfdir}/sysconfig/thermos-observer


%changelog
* Mon Aug 31 2015 Bill Farner <wfarner@apache.org> 0.9.0-1.el7
- Apache Aurora 0.9.0
