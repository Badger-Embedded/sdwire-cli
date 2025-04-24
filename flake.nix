{
  description = "CLI for Badgerd SDWire Devices";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/master";
    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        # packages.default = pkgs.callPackage ./default.nix { };
        packages.default = pkgs.python3Packages.callPackage ./default.nix { };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python3
            poetry
            (self.packages.${system}.default)
          ];
        };
      }
    );
}
