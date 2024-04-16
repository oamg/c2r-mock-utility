%global __python %{__python2}

Name:       convert2rhel
Version:    420.0.1
Release:    1%{?dist}
Summary:    RPM package to mock the behavior of original C2R for testing purposes
License:    GPLv3+
BuildArch:  noarch
BuildRequires:  python2
Requires:       python2
URL:        https://github.com/oamg/c2r-mock-utility
Source0:    https://github.com/oamg/c2r-mock-utility/release/%{name}-%{version}.tar.gz

%description
# Only for testing purposes

%prep
%setup -q

%build
# No setup.py file present

%install
rm -rf %{buildroot}%{python_sitelib}/data

# Create the /usr/share/convert2rhel/ directory for storing data files
install -d %{buildroot}%{_datadir}/%{name}/
cp -a data/. \
    %{buildroot}%{_datadir}/%{name}

install -m 755 -d %{buildroot}%{_bindir}/
cp -a convert2rhel.py \
    %{buildroot}%{_bindir}/%{name}
chmod 755 %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}
%{_datadir}/%{name}/

%changelog
* Mon Apr 16 2024 Martin Litwora <mlitwora@redhat.com>
- First initial build (huzzahh!)
