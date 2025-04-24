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

buildPythonPackage rec {
  pname = "sdwire-cli";
  version = "0.2.4-dev";
  pyproject = true;

  disabled = pythonOlder "3.10";
  src = fetchFromGitHub {
    owner = "badger-embedded";
    repo = pname;
    rev = "main";
    hash = "sha256-Ztp3RzqLE6NSCZGjOaemC62jaGSgPPxDe1esNTfF75c=";
  };

  nativeBuildInputs = [
    poetry-core
  ];

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
