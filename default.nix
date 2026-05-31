{
  lib,
  fetchFromGitHub,
  python3,
  ...
}@args:

python3.pkgs.buildPythonApplication rec {
  pname = "sdwire-cli";
  version = "0.2.4-dev";
  pyproject = true;

  disabled = python3.pkgs.pythonOlder "3.10";
  src = fetchFromGitHub {
    owner = "badger-embedded";
    repo = pname;
    rev = "main";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  nativeBuildInputs = with python3.pkgs; [
    poetry-core
  ];

  propagatedBuildInputs = with python3.pkgs; [
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
