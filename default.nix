{
  lib,
  python3,
  ...
}:

python3.pkgs.buildPythonApplication {
  pname = "sdwire-cli";
  version = "0.4.0";
  pyproject = true;

  disabled = python3.pkgs.pythonOlder "3.10";
  src = ./.;

  nativeBuildInputs = with python3.pkgs; [
    poetry-core
    pythonRelaxDepsHook
  ];

  pythonRelaxDeps = [ "pyftdi" ];

  propagatedBuildInputs = with python3.pkgs; [
    click
    pyusb
    pyftdi
  ];

  postInstall = ''
    install -Dm644 udev/90-sdwire.rules $out/lib/udev/rules.d/90-sdwire.rules
  '';

  pythonImportsCheck = [ "sdwire" ];

  meta = with lib; {
    description = "CLI for Badgerd SDWire Devices";
    homepage = "https://github.com/Badger-Embedded/sdwire-cli";
    license = licenses.gpl3;
    mainProgram = "sdwire";
    maintainers = with maintainers; [ talhaHavadar ];
  };
}
