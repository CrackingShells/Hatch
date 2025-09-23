## [0.7.0-dev.1](https://github.com/CrackingShells/Hatch/compare/v0.6.3...v0.7.0-dev.1) (2025-09-23)


### Features

* **cli:** implement hatch mcp sync command with advanced options ([f5eceb0](https://github.com/CrackingShells/Hatch/commit/f5eceb0389cd588477f331f4c22ba030715d5f75))
* **cli:** implement object-action pattern for MCP remove commands ([7c619a2](https://github.com/CrackingShells/Hatch/commit/7c619a238e195a57be63702c28edd0cb43015392))
* enhance package management with MCP host configuration integration ([0de6e51](https://github.com/CrackingShells/Hatch/commit/0de6e510ad255e932a16693c55fcc1bc069458fa))
* implement comprehensive host configuration tracking system ([f7bfc1e](https://github.com/CrackingShells/Hatch/commit/f7bfc1e8018533321e5a3987a265ac7c09cf9ce4))
* implement consolidated MCPServerConfig Pydantic model ([e984a82](https://github.com/CrackingShells/Hatch/commit/e984a82d1b56fe98e01731c4a8027b3248ab8482))
* implement decorator-based strategy registration system ([b424520](https://github.com/CrackingShells/Hatch/commit/b424520e26156a1186d7444b59f7e096485bff85))
* implement host strategy classes with inheritance architecture ([1e8d95b](https://github.com/CrackingShells/Hatch/commit/1e8d95b65782de4c2859d6889737e74dd8f87c09))
* implement MCP backup management commands (Phase 3d) ([3be7e27](https://github.com/CrackingShells/Hatch/commit/3be7e27b94a9eddb60b2ca5325b3bf5cb1db3761))
* implement MCP host configuration backup system ([de661e2](https://github.com/CrackingShells/Hatch/commit/de661e2982f6804283fd5205b8dd9402e94f5b80))
* implement MCP host discovery and listing commands (Phase 3c) ([23dba35](https://github.com/CrackingShells/Hatch/commit/23dba35da56015d965c895b937f3e5e18b87808b))
* implement package-MCP integration with existing APIs ([9d9cb1f](https://github.com/CrackingShells/Hatch/commit/9d9cb1f444f0ab5cec88bcd77658135f3fa93cb4))
* integrate MCP host configuration modules with decorator registration ([a6bf902](https://github.com/CrackingShells/Hatch/commit/a6bf902b95c7c7ea42758186782c8f45968e3ad3))
* **mcp:** add host configuration removal functionality ([921b351](https://github.com/CrackingShells/Hatch/commit/921b351be827dd718e21cf9b2d042065f53f81ed))
* **mcp:** implement advanced synchronization backend ([97ed2b6](https://github.com/CrackingShells/Hatch/commit/97ed2b6713251605ceb72e6c391b0e6135c57632))


### Bug Fixes

* **ci:** plugin definition structure ([d28d54c](https://github.com/CrackingShells/Hatch/commit/d28d54c36a68d59925ced4ee80fe961d5074035d))
* **ci:** using custom `@artessan-devs/sr-uv-plugin` ([c23c2dd](https://github.com/CrackingShells/Hatch/commit/c23c2dd6885a282b5ab5b41306d6d907d836e2b9))
* **cli:** string value usage ([f48fd23](https://github.com/CrackingShells/Hatch/commit/f48fd23bfa5f9b5ed3c27640afb2f45573449471))
* **deps:** add pydantic dep ([bb83b4f](https://github.com/CrackingShells/Hatch/commit/bb83b4fc0c38f7bb6927a7b6585a5d1851e30e19))
* implement environment-specific Python executable path resolution ([ec7efe3](https://github.com/CrackingShells/Hatch/commit/ec7efe3471a5484ebf0d807bdbb6332f4d196b88))
* implement functional backup restore system resolving production failures ([1f2fd35](https://github.com/CrackingShells/Hatch/commit/1f2fd35c0059cd46dfe9d5c2ab4f5cbe38163337))
* replace blocking input() with TTY-aware request_confirmation ([7936b1f](https://github.com/CrackingShells/Hatch/commit/7936b1f52809b38a8fdefc6139e96c4bd25499a8))
* resolve all MCP CLI test failures achieving 100% pass rate ([b98a569](https://github.com/CrackingShells/Hatch/commit/b98a5696975c67fbe481a5f9ebf956fa04b639bc))
* resolve backup system filename format bug causing discovery failures ([d32c102](https://github.com/CrackingShells/Hatch/commit/d32c1021b4644566c0e01a54e7932f5a4bb97db3))
* resolve configuration file corruption and data loss issues ([65e32cd](https://github.com/CrackingShells/Hatch/commit/65e32cd5f0fad26680efc99ac7044a708979f09e))
* resolve non-TTY environment blocking in request_confirmation ([c077748](https://github.com/CrackingShells/Hatch/commit/c0777488b5a16fedb29cac5a4148bc16072d25df))
* **test:** resolve failing integration tests with proper error handling ([af940a1](https://github.com/CrackingShells/Hatch/commit/af940a1a4a810db094f0980ca3cae731461e463c))
* use the FastMCP instance and not HatchMCP ([9be1a2c](https://github.com/CrackingShells/Hatch/commit/9be1a2c330b2f4eee9e68de59931065d3573f4cf))


### Documentation

* add comprehensive MCP host configuration documentation ([24b3e55](https://github.com/CrackingShells/Hatch/commit/24b3e55e9c0058eb921b3ab22d03541e4a1251cb))
* add MCP backup system architecture documentation ([de7d16a](https://github.com/CrackingShells/Hatch/commit/de7d16aaf728e671b0046f21da242e41f204b69e))
* **mcp:** add comprehensive synchronization command documentation ([445a73f](https://github.com/CrackingShells/Hatch/commit/445a73f3e60aa3cc33d929c03ad2efe77f41de46))
* **mcp:** add user guide for direct management commands ([428c996](https://github.com/CrackingShells/Hatch/commit/428c99676724a57949da3ce1358609f541ab56c0))
* **mcp:** streamline architecture documentation ([14f93a0](https://github.com/CrackingShells/Hatch/commit/14f93a01b34f5834af464bf52086c4dbf8004409))
* rewrite MCP host configuration documentation to organizational standards ([8deb027](https://github.com/CrackingShells/Hatch/commit/8deb027abbd5565b4cdfbb7013d606a507136705))


### Code Refactoring

* directory name ([c5858ff](https://github.com/CrackingShells/Hatch/commit/c5858ff9fdaf56e0dbf25f71690538494e19b38e))
* **test:** mark tests taking around 30 secs as slow. ([6bcc321](https://github.com/CrackingShells/Hatch/commit/6bcc321b151f97377187f7158378ae7fbef3ed6f))

## [0.6.3](https://github.com/CrackingShells/Hatch/compare/v0.6.2...v0.6.3) (2025-09-18)


### Features

* add centralized test data infrastructure for non-TTY testing ([a704937](https://github.com/CrackingShells/Hatch/commit/a70493751e8e74de5b10e79df55088c7a99ad15c))
* add non-TTY handling to dependency installation orchestrator ([ee63d6e](https://github.com/CrackingShells/Hatch/commit/ee63d6eb043fab611100f06ca4fbf0ea89bba711))
* add wobble decorators to test_docker_installer.py ([66740f8](https://github.com/CrackingShells/Hatch/commit/66740f8154e9161c52535c6bea7bbe3b1db40221))
* add wobble decorators to test_env_manip.py ([ec6e0a2](https://github.com/CrackingShells/Hatch/commit/ec6e0a2f17be9c395ab6ef9fac4dfab2d3f317e9))
* add wobble decorators to test_online_package_loader.py ([34b8173](https://github.com/CrackingShells/Hatch/commit/34b8173b9c95768b325e752e9f87785e2785e42d))
* add wobble decorators to test_python_environment_manager.py ([251b0d8](https://github.com/CrackingShells/Hatch/commit/251b0d86fc2a534b1913b2ec1943946082a16f8a))
* add wobble decorators to test_registry_retriever.py ([0bc43fe](https://github.com/CrackingShells/Hatch/commit/0bc43fef091ecae6a55c2c0f5b43f14d86e05132))
* add wobble decorators to test_system_installer.py ([26707b5](https://github.com/CrackingShells/Hatch/commit/26707b574e1712a966d05dd8d8d3300b16d6ec5d))
* complete wobble test categorization ([5a11d45](https://github.com/CrackingShells/Hatch/commit/5a11d451e6e75429483cbc2b8fd996c2bd8349ac))
* implement self-contained test data architecture with 15 core packages ([c7a2fae](https://github.com/CrackingShells/Hatch/commit/c7a2fae40d93ccc9f0c1fd28edb42877541b6781))


### Bug Fixes

* add missing wobble decorators to remaining test files ([e3a1c92](https://github.com/CrackingShells/Hatch/commit/e3a1c928ac3eea81e1a7274252f4ccf63c73559f))
* add required scope parameters to integration test decorators ([ca9cf65](https://github.com/CrackingShells/Hatch/commit/ca9cf65ee683dd78831d81284f235b67f3459347))
* correct wobble integration_test decorator usage ([faf3344](https://github.com/CrackingShells/Hatch/commit/faf3344103845b3e320bee99e386011acd1cce89))
* migrate failing tests to use self-contained test packages ([33c5782](https://github.com/CrackingShells/Hatch/commit/33c578201d4065aba344c27a996523253063667e))
* resolve critical test failures in architecture migration ([c3c3575](https://github.com/CrackingShells/Hatch/commit/c3c3575c3976295355c873b1a02159aa4cb3418e))


### Documentation

* add comprehensive documentation for non-TTY handling ([65c1efb](https://github.com/CrackingShells/Hatch/commit/65c1efb6d0df47f76eb11fe17ff7a091eaec4a4f))
* add mkdocs-print-site-plugin ([#37](https://github.com/CrackingShells/Hatch/issues/37)) ([dd86960](https://github.com/CrackingShells/Hatch/commit/dd869601a81f0cfcef4f905485f2db5572fc43cb))
* enable code copy feature in mkdocs.yml ([300c114](https://github.com/CrackingShells/Hatch/commit/300c114fbc9ad124782dc202ae6e969f50cd635c))
* enable Python requirements installation for documentation build ([#35](https://github.com/CrackingShells/Hatch/issues/35)) ([ea53013](https://github.com/CrackingShells/Hatch/commit/ea530130d3893fdf2e0f4feddcf9606ba797802f))
* enhance documentation with API reference and mkdocstrings integration ([#34](https://github.com/CrackingShells/Hatch/issues/34)) ([b99c964](https://github.com/CrackingShells/Hatch/commit/b99c9642cbb6bca3d2906b476bb92626816d66ef))
* moving from GitHub Pages to Read The Docs ([#32](https://github.com/CrackingShells/Hatch/issues/32)) ([9b7dd07](https://github.com/CrackingShells/Hatch/commit/9b7dd07e9f84637408518c30cfed4f5a79329faa))
* update documentation theme to Material and add mkdocs-material dependency ([#36](https://github.com/CrackingShells/Hatch/issues/36)) ([5fd9a40](https://github.com/CrackingShells/Hatch/commit/5fd9a40897a1a3d8d4930b08bf1496c2ecf3d480))


### Code Refactoring

* eliminate redundant dynamic test package generation ([f497c09](https://github.com/CrackingShells/Hatch/commit/f497c0997e7ae2a3cdf417848f533e42dbf323fd))
* remove sys.path.insert statements from test files ([41c291e](https://github.com/CrackingShells/Hatch/commit/41c291ee9da12d70f1f16a0eebef32cb9bd11444))

## [0.6.3-dev.1](https://github.com/CrackingShells/Hatch/compare/v0.6.2...v0.6.3-dev.1) (2025-09-18)


### Features

* add centralized test data infrastructure for non-TTY testing ([a704937](https://github.com/CrackingShells/Hatch/commit/a70493751e8e74de5b10e79df55088c7a99ad15c))
* add non-TTY handling to dependency installation orchestrator ([ee63d6e](https://github.com/CrackingShells/Hatch/commit/ee63d6eb043fab611100f06ca4fbf0ea89bba711))
* add wobble decorators to test_docker_installer.py ([66740f8](https://github.com/CrackingShells/Hatch/commit/66740f8154e9161c52535c6bea7bbe3b1db40221))
* add wobble decorators to test_env_manip.py ([ec6e0a2](https://github.com/CrackingShells/Hatch/commit/ec6e0a2f17be9c395ab6ef9fac4dfab2d3f317e9))
* add wobble decorators to test_online_package_loader.py ([34b8173](https://github.com/CrackingShells/Hatch/commit/34b8173b9c95768b325e752e9f87785e2785e42d))
* add wobble decorators to test_python_environment_manager.py ([251b0d8](https://github.com/CrackingShells/Hatch/commit/251b0d86fc2a534b1913b2ec1943946082a16f8a))
* add wobble decorators to test_registry_retriever.py ([0bc43fe](https://github.com/CrackingShells/Hatch/commit/0bc43fef091ecae6a55c2c0f5b43f14d86e05132))
* add wobble decorators to test_system_installer.py ([26707b5](https://github.com/CrackingShells/Hatch/commit/26707b574e1712a966d05dd8d8d3300b16d6ec5d))
* complete wobble test categorization ([5a11d45](https://github.com/CrackingShells/Hatch/commit/5a11d451e6e75429483cbc2b8fd996c2bd8349ac))
* implement self-contained test data architecture with 15 core packages ([c7a2fae](https://github.com/CrackingShells/Hatch/commit/c7a2fae40d93ccc9f0c1fd28edb42877541b6781))


### Bug Fixes

* add missing wobble decorators to remaining test files ([e3a1c92](https://github.com/CrackingShells/Hatch/commit/e3a1c928ac3eea81e1a7274252f4ccf63c73559f))
* add required scope parameters to integration test decorators ([ca9cf65](https://github.com/CrackingShells/Hatch/commit/ca9cf65ee683dd78831d81284f235b67f3459347))
* correct wobble integration_test decorator usage ([faf3344](https://github.com/CrackingShells/Hatch/commit/faf3344103845b3e320bee99e386011acd1cce89))
* migrate failing tests to use self-contained test packages ([33c5782](https://github.com/CrackingShells/Hatch/commit/33c578201d4065aba344c27a996523253063667e))
* resolve critical test failures in architecture migration ([c3c3575](https://github.com/CrackingShells/Hatch/commit/c3c3575c3976295355c873b1a02159aa4cb3418e))


### Documentation

* add comprehensive documentation for non-TTY handling ([65c1efb](https://github.com/CrackingShells/Hatch/commit/65c1efb6d0df47f76eb11fe17ff7a091eaec4a4f))
* add mkdocs-print-site-plugin ([#37](https://github.com/CrackingShells/Hatch/issues/37)) ([dd86960](https://github.com/CrackingShells/Hatch/commit/dd869601a81f0cfcef4f905485f2db5572fc43cb))
* enable code copy feature in mkdocs.yml ([300c114](https://github.com/CrackingShells/Hatch/commit/300c114fbc9ad124782dc202ae6e969f50cd635c))
* enable Python requirements installation for documentation build ([#35](https://github.com/CrackingShells/Hatch/issues/35)) ([ea53013](https://github.com/CrackingShells/Hatch/commit/ea530130d3893fdf2e0f4feddcf9606ba797802f))
* enhance documentation with API reference and mkdocstrings integration ([#34](https://github.com/CrackingShells/Hatch/issues/34)) ([b99c964](https://github.com/CrackingShells/Hatch/commit/b99c9642cbb6bca3d2906b476bb92626816d66ef))
* moving from GitHub Pages to Read The Docs ([#32](https://github.com/CrackingShells/Hatch/issues/32)) ([9b7dd07](https://github.com/CrackingShells/Hatch/commit/9b7dd07e9f84637408518c30cfed4f5a79329faa))
* update documentation theme to Material and add mkdocs-material dependency ([#36](https://github.com/CrackingShells/Hatch/issues/36)) ([5fd9a40](https://github.com/CrackingShells/Hatch/commit/5fd9a40897a1a3d8d4930b08bf1496c2ecf3d480))


### Code Refactoring

* eliminate redundant dynamic test package generation ([f497c09](https://github.com/CrackingShells/Hatch/commit/f497c0997e7ae2a3cdf417848f533e42dbf323fd))
* remove sys.path.insert statements from test files ([41c291e](https://github.com/CrackingShells/Hatch/commit/41c291ee9da12d70f1f16a0eebef32cb9bd11444))
