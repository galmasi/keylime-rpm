%global srcname keylime
%define _unpackaged_files_terminate_build 0

Name:    keylime
Version: 6.1.0
Release: 1%{?dist}
Summary: Open source TPM software for Bootstrapping and Maintaining Trust

BuildArch:      noarch

URL:            https://github.com/keylime/keylime
Source0:        https://github.com/keylime/keylime/archive/%{version}.tar.gz
# Main program: BSD
# Icons: MIT
License: ASL 2.0 and MIT

BuildRequires: python3-setuptools
BuildRequires: systemd
BuildRequires: systemd-rpm-macros

Requires: procps-ng
Requires: python3-pyasn1
Requires: python3-pyyaml
Requires: python3-m2crypto
Requires: python3-cryptography
Requires: python3-tornado
Requires: python3-simplejson
Requires: python3-requests
Requires: python3-zmq
Requires: python3-gnupg
Requires: tpm2-tss
Requires: tpm2-tools

%description
Keylime is a TPM based highly scalable remote boot attestation
and runtime integrity measurement solution.

%prep
%autosetup -n %{srcname}-%{version}

%build
%py3_build

%install
%py3_install
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}/%{_sharedstatedir}/keylime

install -pm 644 %{srcname}.conf \
    %{buildroot}%{_sysconfdir}/%{srcname}.conf

# make up for the fact that py3_install installed stuff we don't want.

rm %{buildroot}/usr/bin/keylime_registrar
rm %{buildroot}/usr/bin/keylime_verifier
rm %{buildroot}/usr/bin/keylime_webapp
rm %{buildroot}/usr/bin/keylime_tenant

# generate a new keylime agent service file
# with the correct start interval, bursts, and users.
# using tpmrm0 not abrmd.

cat <<EOF > ./keylime_agent.service
[Unit]
Description=The Keylime compute agent
StartLimitInterval=10s
StartLimitBurst=5

[Service]
User=keylime
Group=tss
Environment=TPM2TOOLS_TCTI=device:/dev/tpmrm0
ExecStart=/usr/bin/keylime_agent
TimeoutSec=60s
Restart=on-failure
RestartSec=120s

[Install]
WantedBy=default.target
EOF

install -pm 644 ./keylime_agent.service %{buildroot}%{_unitdir}/keylime_agent.service

cp -r ./tpm_cert_store %{buildroot}%{_sharedstatedir}/keylime/

%post

# creating tss group if he isn't already there
if ! getent group tss >/dev/null; then
    groupadd --system tss
fi

# creating tss user if he isn't already there
if ! getent passwd tss >/dev/null; then
    adduser --system -g tss --shell /bin/false \
            --home /var/lib/tpm --no-create-home \
            --comment "TPM software stack" \
            tss
fi

# creating keylime user if he isn't already there
if ! getent passwd keylime >/dev/null; then
    adduser --system -g tss --shell /bin/false \
            --home /var/lib/keylime --no-create-home \
            --comment "Keylime remote attestation" \
            keylime
fi

# Create keylime operational directory
mkdir -p /var/lib/keylime/secure

# Only root can mount tmpfs with `-o` 
if ! grep -qs '/var/lib/keylime/secure ' /proc/mounts ; then mount -t tmpfs -o size=1m,mode=0700 tmpfs /var/lib/keylime/secure
fi

# Setting owner
chown -R keylime:tss /var/lib/keylime

# The "keylime" user belongs to tss, and we need to give access to /sys/kernel/security/<x>
# TODO these only work for one boot.

if [ -d /sys/kernel/security/tpm0 ] ; then
    chown -R tss:tss /sys/kernel/security/tpm0
fi

if [ -d /sys/kernel/security/ima ] ; then
    chown -R tss:tss /sys/kernel/security/ima
fi

%systemd_post %{srcname}_agent.service

%preun
%systemd_preun %{srcname}_agent.service

%postun
%systemd_postun_with_restart %{srcname}_agent.service

%files
%license LICENSE keylime/static/icons/ICON-LICENSE
%doc README.md
%{python3_sitelib}/%{srcname}-*.egg-info/
%{python3_sitelib}/%{srcname}
%{_bindir}/%{srcname}_agent
%{_bindir}/%{srcname}_ca
%{_bindir}/%{srcname}_migrations_apply
%{_bindir}/%{srcname}_provider_platform_init
%{_bindir}/%{srcname}_provider_registrar
%{_bindir}/%{srcname}_provider_vtpm_add
%{_bindir}/%{srcname}_userdata_encrypt
%{_bindir}/%{srcname}_ima_emulator
%config(noreplace) %{_sysconfdir}/%{srcname}.conf
%{_unitdir}/*
%{_sharedstatedir}/keylime/tpm_cert_store/*

%changelog
* Wed Feb 24 2021 Luke Hinds <lhinds@redhat.com> 6.0.0-1
- Updating for Keylime release v6.0.0

* Tue Feb 02 2021 Luke Hinds <lhinds@redhat.com> 5.8.1-1
- Updating for Keylime release v5.8.1

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 5.8.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Sat Jan 23 2021 Luke Hinds <lhinds@redhat.com> 5.8.0-1
- Updating for Keylime release v5.8.0

* Fri Jul 17 2020 Luke Hinds <lhinds@redhat.com> 5.7.2-1
- Updating for Keylime release v5.7.2

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 5.6.2-2
- Rebuilt for Python 3.9

* Fri May 01 2020 Luke Hinds <lhinds@redhat.com> 5.6.2-1
- Updating for Keylime release v5.6.2

* Thu Feb 06 2020 Luke Hinds <lhinds@redhat.com> 5.5.0-1
- Updating for Keylime release v5.5.0

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 5.4.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Dec 12 2019 Luke Hinds <lhinds@redhat.com> 5.4.1-1
– Initial Packaging
