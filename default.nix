{
  lib,
  buildPythonPackage,
  fetchFromGitHub,
  poetry-core,
  python,
  pythonRelaxDepsHook,
  pythonOlder,
  ...
}@args:

# let
#   # If you need to relax dependencies (common with Poetry projects)
#   relaxedDeps = [ "some-dependency" ]; # Add your problematic dependencies here
# in

buildPythonPackage rec {
  pname = "sdwire-cli";
  version = "0.2.4";
  pyproject = true;

  disabled = pythonOlder "3.10";
  src = fetchFromGitHub {
    owner = "talhaHavadar";
    repo = pname;
    rev = "main"; # or your commit hash
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  # postPatch = ''
  #   # Remove dependency constraints that might cause issues in Nix
  #   substituteInPlace pyproject.toml \
  #     --replace 'some-dependency = "^1.2.3"' 'some-dependency = "*"'
  # '';

  nativeBuildInputs = [
    poetry-core
    # pythonRelaxDepsHook
  ];

  # pythonRelaxDeps = relaxedDeps;

  propagatedBuildInputs = with python.pkgs; [
    click
    pyusb
    pyftdi
    pyudev
  ];

  pythonImportsCheck = [ "sdwire" ];

  meta = with lib; {
    description = "CLI for Badgerd SDWire Devices";
    homepage = "https://github.com/Badger-Embedded/sdwire-cli";
    license = licenses.gpl3;
    maintainers = with maintainers; [ talhaHavadar ];
  };
}
