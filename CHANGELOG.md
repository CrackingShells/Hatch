## 0.8.0-dev.1 (2026-02-04)

* Merge pull request #44 from LittleCoinCoin/dev ([1157922](https://github.com/CrackingShells/Hatch/commit/1157922)), closes [#44](https://github.com/CrackingShells/Hatch/issues/44)
* chore: update entry point to hatch.cli module ([cf81671](https://github.com/CrackingShells/Hatch/commit/cf81671))
* chore: update submodule `cracking-shells-playbook` ([222b357](https://github.com/CrackingShells/Hatch/commit/222b357))
* chore(deps): add pytest to dev dependencies ([2761afe](https://github.com/CrackingShells/Hatch/commit/2761afe))
* chore(docs): remove deprecated CLI api doc ([12a22c0](https://github.com/CrackingShells/Hatch/commit/12a22c0))
* chore(docs): remove deprecated MCP documentation files ([5ca09a3](https://github.com/CrackingShells/Hatch/commit/5ca09a3))
* chore(tests): remove deprecated MCP test files ([29a5ec5](https://github.com/CrackingShells/Hatch/commit/29a5ec5))
* fix(backup): support different config filenames in backup listing ([06eb53a](https://github.com/CrackingShells/Hatch/commit/06eb53a)), closes [#2](https://github.com/CrackingShells/Hatch/issues/2)
* fix(docs): add missing return type annotations for mkdocs build ([da78682](https://github.com/CrackingShells/Hatch/commit/da78682))
* docs: fix broken link in MCP host configuration architecture ([e9f89f1](https://github.com/CrackingShells/Hatch/commit/e9f89f1))
* docs(api): restructure CLI API documentation to modular architecture ([318d212](https://github.com/CrackingShells/Hatch/commit/318d212))
* docs(cli-ref): mark package list as deprecated and update filters ([06f5b75](https://github.com/CrackingShells/Hatch/commit/06f5b75))
* docs(cli-ref): update environment commands section ([749d992](https://github.com/CrackingShells/Hatch/commit/749d992))
* docs(cli-ref): update MCP commands section with new list/show commands ([1c812fd](https://github.com/CrackingShells/Hatch/commit/1c812fd))
* docs(cli): add module docstrings for refactored CLI ([8d7de20](https://github.com/CrackingShells/Hatch/commit/8d7de20))
* docs(cli): update documentation for handler-based architecture ([f95c5d0](https://github.com/CrackingShells/Hatch/commit/f95c5d0))
* docs(devs): add CLI architecture and implementation guide ([a3152e1](https://github.com/CrackingShells/Hatch/commit/a3152e1))
* docs(guide): add quick reference for viewing commands ([5bf5d01](https://github.com/CrackingShells/Hatch/commit/5bf5d01))
* docs(guide): add viewing host configurations section ([6c381d1](https://github.com/CrackingShells/Hatch/commit/6c381d1))
* docs(mcp-host-config): deprecate legacy architecture doc ([d8618a5](https://github.com/CrackingShells/Hatch/commit/d8618a5))
* docs(mcp-host-config): deprecate legacy extension guide ([f172a51](https://github.com/CrackingShells/Hatch/commit/f172a51))
* docs(mcp-host-config): write new architecture documentation ([ff05ad5](https://github.com/CrackingShells/Hatch/commit/ff05ad5))
* docs(mcp-host-config): write new extension guide ([7821062](https://github.com/CrackingShells/Hatch/commit/7821062))
* docs(mcp-reporting): document metadata field exclusion behavior ([5ccb7f9](https://github.com/CrackingShells/Hatch/commit/5ccb7f9))
* docs(tutorial): fix command syntax in environment sync tutorial ([b2f40bf](https://github.com/CrackingShells/Hatch/commit/b2f40bf))
* docs(tutorial): fix verification commands in checkpoint tutorial ([59b2485](https://github.com/CrackingShells/Hatch/commit/59b2485))
* docs(tutorial): update env list output in create environment tutorial ([443607c](https://github.com/CrackingShells/Hatch/commit/443607c))
* docs(tutorial): update package installation tutorial outputs ([588bab3](https://github.com/CrackingShells/Hatch/commit/588bab3))
* docs(tutorials): fix command syntax in 04-mcp-host-configuration ([2ac1058](https://github.com/CrackingShells/Hatch/commit/2ac1058))
* docs(tutorials): fix outdated env list output format in 02-environments ([d38ae24](https://github.com/CrackingShells/Hatch/commit/d38ae24))
* docs(tutorials): fix validation output in 03-author-package ([776d40f](https://github.com/CrackingShells/Hatch/commit/776d40f))
* refactor(cli): add deprecation warning to cli_hatch shim ([f9adf0a](https://github.com/CrackingShells/Hatch/commit/f9adf0a))
* refactor(cli): create cli package structure ([bc80e29](https://github.com/CrackingShells/Hatch/commit/bc80e29))
* refactor(cli): deprecate `mcp discover servers` and `package list` ([9ce5be0](https://github.com/CrackingShells/Hatch/commit/9ce5be0))
* refactor(cli): extract argument parsing and implement clean routing ([efeae24](https://github.com/CrackingShells/Hatch/commit/efeae24))
* refactor(cli): extract environment handlers to cli_env ([d00959f](https://github.com/CrackingShells/Hatch/commit/d00959f))
* refactor(cli): extract handle_mcp_configure to cli_mcp ([9b9bc4d](https://github.com/CrackingShells/Hatch/commit/9b9bc4d))
* refactor(cli): extract handle_mcp_sync to cli_mcp ([f69be90](https://github.com/CrackingShells/Hatch/commit/f69be90))
* refactor(cli): extract MCP backup handlers to cli_mcp ([ca65e2b](https://github.com/CrackingShells/Hatch/commit/ca65e2b))
* refactor(cli): extract MCP discovery handlers to cli_mcp ([887b96e](https://github.com/CrackingShells/Hatch/commit/887b96e))
* refactor(cli): extract MCP list handlers to cli_mcp ([e518e90](https://github.com/CrackingShells/Hatch/commit/e518e90))
* refactor(cli): extract MCP remove handlers to cli_mcp ([4e84be7](https://github.com/CrackingShells/Hatch/commit/4e84be7))
* refactor(cli): extract package handlers to cli_package ([ebecb1e](https://github.com/CrackingShells/Hatch/commit/ebecb1e))
* refactor(cli): extract shared utilities to cli_utils ([0b0dc92](https://github.com/CrackingShells/Hatch/commit/0b0dc92))
* refactor(cli): extract system handlers to cli_system ([2f7d715](https://github.com/CrackingShells/Hatch/commit/2f7d715))
* refactor(cli): integrate backup path into ResultReporter ([fd9a1f4](https://github.com/CrackingShells/Hatch/commit/fd9a1f4))
* refactor(cli): integrate sync statistics into ResultReporter ([cc5a8b2](https://github.com/CrackingShells/Hatch/commit/cc5a8b2))
* refactor(cli): normalize cli_utils warning messages ([6e9b983](https://github.com/CrackingShells/Hatch/commit/6e9b983))
* refactor(cli): normalize MCP warning messages ([b72c6a4](https://github.com/CrackingShells/Hatch/commit/b72c6a4))
* refactor(cli): normalize operation cancelled messages ([ab0b611](https://github.com/CrackingShells/Hatch/commit/ab0b611))
* refactor(cli): normalize package warning messages ([c7463b3](https://github.com/CrackingShells/Hatch/commit/c7463b3))
* refactor(cli): remove --pattern from mcp list servers ([b8baef9](https://github.com/CrackingShells/Hatch/commit/b8baef9))
* refactor(cli): remove legacy mcp show <host> command ([fd2c290](https://github.com/CrackingShells/Hatch/commit/fd2c290))
* refactor(cli): rewrite mcp list hosts for host-centric design ([ac88a84](https://github.com/CrackingShells/Hatch/commit/ac88a84))
* refactor(cli): rewrite mcp list servers for host-centric design ([c2de727](https://github.com/CrackingShells/Hatch/commit/c2de727))
* refactor(cli): simplify CLI to use unified MCPServerConfig with adapters ([d97b99e](https://github.com/CrackingShells/Hatch/commit/d97b99e))
* refactor(cli): simplify env list to show package count only ([3045718](https://github.com/CrackingShells/Hatch/commit/3045718))
* refactor(cli): update env execution errors to use report_error ([8021ba2](https://github.com/CrackingShells/Hatch/commit/8021ba2))
* refactor(cli): update env validation error to use ValidationError ([101eba7](https://github.com/CrackingShells/Hatch/commit/101eba7))
* refactor(cli): update MCP exception handlers to use report_error ([edec31d](https://github.com/CrackingShells/Hatch/commit/edec31d))
* refactor(cli): update MCP validation errors to use ValidationError ([20b165a](https://github.com/CrackingShells/Hatch/commit/20b165a))
* refactor(cli): update package errors to use report_error ([4d0ab73](https://github.com/CrackingShells/Hatch/commit/4d0ab73))
* refactor(cli): update system errors to use report_error ([b205032](https://github.com/CrackingShells/Hatch/commit/b205032))
* refactor(cli): use HatchArgumentParser for all parsers ([4b750fa](https://github.com/CrackingShells/Hatch/commit/4b750fa))
* refactor(cli): use ResultReporter in env create/remove handlers ([d0991ba](https://github.com/CrackingShells/Hatch/commit/d0991ba))
* refactor(cli): use ResultReporter in env python handlers ([df14f66](https://github.com/CrackingShells/Hatch/commit/df14f66))
* refactor(cli): use ResultReporter in handle_env_python_add_hatch_mcp ([0ec6b6a](https://github.com/CrackingShells/Hatch/commit/0ec6b6a))
* refactor(cli): use ResultReporter in handle_env_use ([b7536fb](https://github.com/CrackingShells/Hatch/commit/b7536fb))
* refactor(cli): use ResultReporter in handle_mcp_configure ([5f3c60c](https://github.com/CrackingShells/Hatch/commit/5f3c60c))
* refactor(cli): use ResultReporter in handle_mcp_sync ([9d52d24](https://github.com/CrackingShells/Hatch/commit/9d52d24))
* refactor(cli): use ResultReporter in handle_package_add ([49585fa](https://github.com/CrackingShells/Hatch/commit/49585fa))
* refactor(cli): use ResultReporter in handle_package_remove ([58ffdf1](https://github.com/CrackingShells/Hatch/commit/58ffdf1))
* refactor(cli): use ResultReporter in handle_package_sync ([987b9d1](https://github.com/CrackingShells/Hatch/commit/987b9d1))
* refactor(cli): use ResultReporter in MCP backup handlers ([9ec9e7b](https://github.com/CrackingShells/Hatch/commit/9ec9e7b))
* refactor(cli): use ResultReporter in MCP remove handlers ([e727324](https://github.com/CrackingShells/Hatch/commit/e727324))
* refactor(cli): use ResultReporter in system handlers ([df64898](https://github.com/CrackingShells/Hatch/commit/df64898))
* refactor(cli): use TableFormatter in handle_env_list ([0f18682](https://github.com/CrackingShells/Hatch/commit/0f18682))
* refactor(cli): use TableFormatter in handle_mcp_backup_list ([17dd96a](https://github.com/CrackingShells/Hatch/commit/17dd96a))
* refactor(cli): use TableFormatter in handle_mcp_discover_hosts ([6bef0fa](https://github.com/CrackingShells/Hatch/commit/6bef0fa))
* refactor(cli): use TableFormatter in handle_mcp_list_hosts ([3b465bb](https://github.com/CrackingShells/Hatch/commit/3b465bb))
* refactor(cli): use TableFormatter in handle_mcp_list_servers ([3145e47](https://github.com/CrackingShells/Hatch/commit/3145e47))
* refactor(mcp-host-config): unified MCPServerConfig ([ca0e51c](https://github.com/CrackingShells/Hatch/commit/ca0e51c))
* refactor(mcp-host-config): update module exports ([5371a43](https://github.com/CrackingShells/Hatch/commit/5371a43))
* refactor(mcp-host-config): wire all strategies to use adapters ([528e5f5](https://github.com/CrackingShells/Hatch/commit/528e5f5))
* refactor(mcp): deprecate display_report in favor of ResultReporter ([3880ea3](https://github.com/CrackingShells/Hatch/commit/3880ea3))
* refactor(models): remove legacy host-specific models from models.py ([ff92280](https://github.com/CrackingShells/Hatch/commit/ff92280))
* feat(adapters): create AdapterRegistry for host-adapter mapping ([a8e3dfb](https://github.com/CrackingShells/Hatch/commit/a8e3dfb))
* feat(adapters): create BaseAdapter abstract class ([4d9833c](https://github.com/CrackingShells/Hatch/commit/4d9833c))
* feat(adapters): create host-specific adapters ([7b725c8](https://github.com/CrackingShells/Hatch/commit/7b725c8))
* feat(cli): add --dry-run to env and package commands ([4a0f3e5](https://github.com/CrackingShells/Hatch/commit/4a0f3e5))
* feat(cli): add --dry-run to env use, package add, create commands ([79da44c](https://github.com/CrackingShells/Hatch/commit/79da44c))
* feat(cli): add --host and --pattern flags to mcp list servers ([29f86aa](https://github.com/CrackingShells/Hatch/commit/29f86aa))
* feat(cli): add --json flag to list commands ([73f62ed](https://github.com/CrackingShells/Hatch/commit/73f62ed))
* feat(cli): add --pattern filter to env list ([6deff84](https://github.com/CrackingShells/Hatch/commit/6deff84))
* feat(cli): add Color, ConsequenceType, Consequence, ResultReporter ([10cdb71](https://github.com/CrackingShells/Hatch/commit/10cdb71))
* feat(cli): add confirmation prompt to env remove ([b1156e7](https://github.com/CrackingShells/Hatch/commit/b1156e7))
* feat(cli): add confirmation prompt to package remove ([38d9051](https://github.com/CrackingShells/Hatch/commit/38d9051))
* feat(cli): add ConversionReport to ResultReporter bridge ([4ea999e](https://github.com/CrackingShells/Hatch/commit/4ea999e))
* feat(cli): add format_info utility ([b1f33d4](https://github.com/CrackingShells/Hatch/commit/b1f33d4))
* feat(cli): add format_validation_error utility ([f28b841](https://github.com/CrackingShells/Hatch/commit/f28b841))
* feat(cli): add format_warning utility ([28ec610](https://github.com/CrackingShells/Hatch/commit/28ec610))
* feat(cli): add hatch env show command ([2bc96bc](https://github.com/CrackingShells/Hatch/commit/2bc96bc))
* feat(cli): add hatch mcp show command ([9ab53bc](https://github.com/CrackingShells/Hatch/commit/9ab53bc))
* feat(cli): add HatchArgumentParser with formatted errors ([1fb7006](https://github.com/CrackingShells/Hatch/commit/1fb7006))
* feat(cli): add highlight utility for entity names ([c25631a](https://github.com/CrackingShells/Hatch/commit/c25631a))
* feat(cli): add parser for env list hosts command ([a218dea](https://github.com/CrackingShells/Hatch/commit/a218dea))
* feat(cli): add parser for env list servers command ([851c866](https://github.com/CrackingShells/Hatch/commit/851c866))
* feat(cli): add parser for mcp show hosts command ([f7abe61](https://github.com/CrackingShells/Hatch/commit/f7abe61))
* feat(cli): add report_error method to ResultReporter ([e0f89e1](https://github.com/CrackingShells/Hatch/commit/e0f89e1))
* feat(cli): add report_partial_success method to ResultReporter ([1ce4fd9](https://github.com/CrackingShells/Hatch/commit/1ce4fd9))
* feat(cli): add TableFormatter for aligned table output ([658f48a](https://github.com/CrackingShells/Hatch/commit/658f48a))
* feat(cli): add true color terminal detection ([aa76bfc](https://github.com/CrackingShells/Hatch/commit/aa76bfc))
* feat(cli): add unicode terminal detection ([91d7c30](https://github.com/CrackingShells/Hatch/commit/91d7c30))
* feat(cli): add ValidationError exception class ([af63b46](https://github.com/CrackingShells/Hatch/commit/af63b46))
* feat(cli): implement env list hosts command ([bebe6ab](https://github.com/CrackingShells/Hatch/commit/bebe6ab))
* feat(cli): implement env list servers command ([0c7a744](https://github.com/CrackingShells/Hatch/commit/0c7a744))
* feat(cli): implement HCL color palette with true color support ([d70b4f2](https://github.com/CrackingShells/Hatch/commit/d70b4f2))
* feat(cli): implement mcp show hosts command ([2c716bb](https://github.com/CrackingShells/Hatch/commit/2c716bb))
* feat(cli): implement mcp show servers command ([e6df7b4](https://github.com/CrackingShells/Hatch/commit/e6df7b4))
* feat(cli): update mcp list hosts JSON output ([a6f5994](https://github.com/CrackingShells/Hatch/commit/a6f5994))
* feat(cli): update mcp list hosts parser with --server flag ([c298d52](https://github.com/CrackingShells/Hatch/commit/c298d52))
* feat(mcp-host-config): add field support constants ([1e81a24](https://github.com/CrackingShells/Hatch/commit/1e81a24))
* feat(mcp-host-config): add transport detection to MCPServerConfig ([c4eabd2](https://github.com/CrackingShells/Hatch/commit/c4eabd2))
* feat(mcp-host-config): implement LMStudioAdapter ([0662b14](https://github.com/CrackingShells/Hatch/commit/0662b14))
* feat(mcp-reporting): metadata fields exclusion from cli reports ([41db3da](https://github.com/CrackingShells/Hatch/commit/41db3da))
* test(cli): add ConversionReport fixtures for reporter tests ([eeccff6](https://github.com/CrackingShells/Hatch/commit/eeccff6))
* test(cli): add failing integration test for MCP handler ([acf7c94](https://github.com/CrackingShells/Hatch/commit/acf7c94))
* test(cli): add failing test for host-centric mcp list servers ([0fcb8fd](https://github.com/CrackingShells/Hatch/commit/0fcb8fd))
* test(cli): add failing tests for ConversionReport integration ([8e6efc0](https://github.com/CrackingShells/Hatch/commit/8e6efc0))
* test(cli): add failing tests for env list hosts ([454b0e4](https://github.com/CrackingShells/Hatch/commit/454b0e4))
* test(cli): add failing tests for env list servers ([7250387](https://github.com/CrackingShells/Hatch/commit/7250387))
* test(cli): add failing tests for host-centric mcp list hosts ([3ec0617](https://github.com/CrackingShells/Hatch/commit/3ec0617))
* test(cli): add failing tests for mcp show hosts ([8c8f3e9](https://github.com/CrackingShells/Hatch/commit/8c8f3e9))
* test(cli): add failing tests for mcp show servers ([fac85fe](https://github.com/CrackingShells/Hatch/commit/fac85fe))
* test(cli): add failing tests for TableFormatter ([90f3953](https://github.com/CrackingShells/Hatch/commit/90f3953))
* test(cli): add test directory structure for CLI reporter ([7044b47](https://github.com/CrackingShells/Hatch/commit/7044b47))
* test(cli): add test utilities for handler testing ([55322c7](https://github.com/CrackingShells/Hatch/commit/55322c7))
* test(cli): add tests for Color enum and color enable/disable logic ([f854324](https://github.com/CrackingShells/Hatch/commit/f854324))
* test(cli): add tests for Consequence dataclass and ResultReporter ([127575d](https://github.com/CrackingShells/Hatch/commit/127575d))
* test(cli): add tests for ConsequenceType enum ([a3f0204](https://github.com/CrackingShells/Hatch/commit/a3f0204))
* test(cli): add tests for error reporting methods ([2561532](https://github.com/CrackingShells/Hatch/commit/2561532))
* test(cli): add tests for HatchArgumentParser ([8b192e5](https://github.com/CrackingShells/Hatch/commit/8b192e5))
* test(cli): add tests for ValidationError and utilities ([a2a5c29](https://github.com/CrackingShells/Hatch/commit/a2a5c29))
* test(cli): add true color detection tests ([79f6faa](https://github.com/CrackingShells/Hatch/commit/79f6faa))
* test(cli): update backup tests for cli_mcp module ([8174bef](https://github.com/CrackingShells/Hatch/commit/8174bef))
* test(cli): update color tests for HCL palette ([a19780c](https://github.com/CrackingShells/Hatch/commit/a19780c))
* test(cli): update direct_management tests for cli_mcp module ([16f8520](https://github.com/CrackingShells/Hatch/commit/16f8520))
* test(cli): update discovery tests for cli_mcp module ([de75cf0](https://github.com/CrackingShells/Hatch/commit/de75cf0))
* test(cli): update for new cli architecture ([64cf74e](https://github.com/CrackingShells/Hatch/commit/64cf74e))
* test(cli): update host config integration tests for cli_mcp module ([ea5c6b6](https://github.com/CrackingShells/Hatch/commit/ea5c6b6))
* test(cli): update host_specific_args tests for cli_mcp module ([8f477f6](https://github.com/CrackingShells/Hatch/commit/8f477f6))
* test(cli): update list tests for cli_mcp module ([e21ecc0](https://github.com/CrackingShells/Hatch/commit/e21ecc0))
* test(cli): update mcp list servers tests for --pattern removal ([9bb5fe5](https://github.com/CrackingShells/Hatch/commit/9bb5fe5))
* test(cli): update partial_updates tests for cli_mcp module ([4484e67](https://github.com/CrackingShells/Hatch/commit/4484e67))
* test(cli): update remaining MCP tests for cli_mcp module ([a655775](https://github.com/CrackingShells/Hatch/commit/a655775))
* test(cli): update sync_functionality tests for cli_mcp module ([eeb2d6d](https://github.com/CrackingShells/Hatch/commit/eeb2d6d))
* test(cli): update tests for cli_utils module ([7d72f76](https://github.com/CrackingShells/Hatch/commit/7d72f76))
* test(cli): update tests for mcp show removal ([a0e730b](https://github.com/CrackingShells/Hatch/commit/a0e730b))
* test(deprecate): rename 28 legacy MCP tests to .bak for rebuild ([e7f9c50](https://github.com/CrackingShells/Hatch/commit/e7f9c50))
* test(mcp-host-config): add adapter registry unit tests ([bc8f455](https://github.com/CrackingShells/Hatch/commit/bc8f455))
* test(mcp-host-config): add integration tests for adapter serialization ([6910120](https://github.com/CrackingShells/Hatch/commit/6910120))
* test(mcp-host-config): add regression tests for field filtering ([d6ce817](https://github.com/CrackingShells/Hatch/commit/d6ce817))
* test(mcp-host-config): add unit tests ([c1a0fa4](https://github.com/CrackingShells/Hatch/commit/c1a0fa4))
* test(mcp-host-config): create three-tier test directory structure ([d78681b](https://github.com/CrackingShells/Hatch/commit/d78681b))
* test(mcp-host-config): update integration tests for adapter architecture ([acd7871](https://github.com/CrackingShells/Hatch/commit/acd7871))


### BREAKING CHANGE

* Remove all legacy host-specific configuration models
that are now replaced by the unified adapter architecture.

Removed models:
- MCPServerConfigBase (abstract base class)
- MCPServerConfigGemini
- MCPServerConfigVSCode
- MCPServerConfigCursor
- MCPServerConfigClaude
- MCPServerConfigKiro
- MCPServerConfigCodex
- MCPServerConfigOmni
- HOST_MODEL_REGISTRY

The unified MCPServerConfig model plus host-specific adapters now
handle all MCP server configuration. See:
- hatch/mcp_host_config/adapters/ for host adapters

This is part of Milestone 3.1: Legacy Removal in the adapter architecture
refactoring. Tests will need to be updated in subsequent commits.

## <small>0.7.1 (2025-12-22)</small>

* Merge pull request #43 from CrackingShells/dev ([b8093b5](https://github.com/CrackingShells/Hatch/commit/b8093b5)), closes [#43](https://github.com/CrackingShells/Hatch/issues/43)
* ci: update pre-release discord notification ([0f618ff](https://github.com/CrackingShells/Hatch/commit/0f618ff))
* ci: update release discord notification ([b7093a0](https://github.com/CrackingShells/Hatch/commit/b7093a0))
* chore: augment code ignore __reports__/ ([b5d59c3](https://github.com/CrackingShells/Hatch/commit/b5d59c3))
* chore: remove dev debug scripts ([391c2da](https://github.com/CrackingShells/Hatch/commit/391c2da))
* chore: remove dev reports ([a7cf3da](https://github.com/CrackingShells/Hatch/commit/a7cf3da))
* chore: update gitignore ([47e0902](https://github.com/CrackingShells/Hatch/commit/47e0902))
* chore(release): 0.7.1-dev.1 ([402eded](https://github.com/CrackingShells/Hatch/commit/402eded))
* chore(release): 0.7.1-dev.2 ([5eb4154](https://github.com/CrackingShells/Hatch/commit/5eb4154))
* chore(release): 0.7.1-dev.3 ([a64a058](https://github.com/CrackingShells/Hatch/commit/a64a058))
* fix: config path handling ([068a856](https://github.com/CrackingShells/Hatch/commit/068a856))
* fix(backup): preserve original filename in backup creation ([79d4b7d](https://github.com/CrackingShells/Hatch/commit/79d4b7d))
* fix(cli): prevent unwanted defaults ([055f019](https://github.com/CrackingShells/Hatch/commit/055f019))
* fix(codex): map http_headers to universal headers field ([308f577](https://github.com/CrackingShells/Hatch/commit/308f577))
* docs(cli): add host labels to configure command help ([8ebf59f](https://github.com/CrackingShells/Hatch/commit/8ebf59f))
* docs(codex): add CLI reference and usage examples ([7a97ee8](https://github.com/CrackingShells/Hatch/commit/7a97ee8))
* docs(codex): update to mention support for Codex ([588def6](https://github.com/CrackingShells/Hatch/commit/588def6))
* docs(dev): enhance MCP host configuration extension guidance ([e4e42ce](https://github.com/CrackingShells/Hatch/commit/e4e42ce))
* docs(kiro): add Kiro to supported MCP hosts across all documentation ([00edf42](https://github.com/CrackingShells/Hatch/commit/00edf42))
* docs(reports): add implementation completion report ([97d386b](https://github.com/CrackingShells/Hatch/commit/97d386b))
* docs(reports): codex CLI enhancement analysis and implementation ([257fe80](https://github.com/CrackingShells/Hatch/commit/257fe80))
* docs(reports): dev specs for Codex MCP config support via Hatch! ([2bb1d3c](https://github.com/CrackingShells/Hatch/commit/2bb1d3c))
* test(codex): add comprehensive CLI argument tests ([9cae56c](https://github.com/CrackingShells/Hatch/commit/9cae56c))
* test(codex): add comprehensive Codex host strategy test suite ([ba8178c](https://github.com/CrackingShells/Hatch/commit/ba8178c))
* test(codex): fix Omni model field name in conversion test ([3a040f2](https://github.com/CrackingShells/Hatch/commit/3a040f2))
* test(kiro): add comprehensive backup integration tests ([09776d2](https://github.com/CrackingShells/Hatch/commit/09776d2))
* test(kiro): implement comprehensive test suite for Kiro MCP integration ([04b3733](https://github.com/CrackingShells/Hatch/commit/04b3733))
* test(kiro): implement test data infrastructure for Kiro MCP integration ([da30374](https://github.com/CrackingShells/Hatch/commit/da30374))
* feat(codex): add CLI arguments for Codex ([e8f6e4e](https://github.com/CrackingShells/Hatch/commit/e8f6e4e))
* feat(codex): add MCPServerConfigCodex model and infrastructure ([ed86ddf](https://github.com/CrackingShells/Hatch/commit/ed86ddf))
* feat(codex): add tomli-w dependency for TOML support ([e1e575d](https://github.com/CrackingShells/Hatch/commit/e1e575d))
* feat(codex): implement CodexHostStrategy with TOML support ([cac2301](https://github.com/CrackingShells/Hatch/commit/cac2301))
* feat(kiro): add configuration file backup support ([f8287f1](https://github.com/CrackingShells/Hatch/commit/f8287f1))
* feat(kiro): add Kiro IDE support to model layer ([a505e28](https://github.com/CrackingShells/Hatch/commit/a505e28))
* feat(kiro): add Kiro-specific arguments to mcp configure command ([cb89045](https://github.com/CrackingShells/Hatch/commit/cb89045))
* feat(kiro): implement KiroHostStrategy for configuration management ([f03e16b](https://github.com/CrackingShells/Hatch/commit/f03e16b))
* feat(mcp-models): map shared tool filtering flags to Codex ([627a556](https://github.com/CrackingShells/Hatch/commit/627a556))

## <small>0.7.1-dev.3 (2025-12-18)</small>

* fix(cli): prevent unwanted defaults ([8a9441b](https://github.com/CrackingShells/Hatch/commit/8a9441b))

## <small>0.7.1-dev.2 (2025-12-15)</small>

* Merge branch 'feat/codex-support' into dev ([b82bf0f](https://github.com/CrackingShells/Hatch/commit/b82bf0f))
* chore: augment code ignore __reports__/ ([bed11cd](https://github.com/CrackingShells/Hatch/commit/bed11cd))
* chore: remove dev debug scripts ([f1880ce](https://github.com/CrackingShells/Hatch/commit/f1880ce))
* chore: remove dev reports ([8c3f455](https://github.com/CrackingShells/Hatch/commit/8c3f455))
* chore: update gitignore ([cd1934a](https://github.com/CrackingShells/Hatch/commit/cd1934a))
* docs(cli): add host labels to configure command help ([842e771](https://github.com/CrackingShells/Hatch/commit/842e771))
* docs(codex): add CLI reference and usage examples ([a68e932](https://github.com/CrackingShells/Hatch/commit/a68e932))
* docs(codex): update to mention support for Codex ([7fa2bdb](https://github.com/CrackingShells/Hatch/commit/7fa2bdb))
* docs(reports): add implementation completion report ([7b67225](https://github.com/CrackingShells/Hatch/commit/7b67225))
* docs(reports): codex CLI enhancement analysis and implementation ([c5327d2](https://github.com/CrackingShells/Hatch/commit/c5327d2))
* docs(reports): dev specs for Codex MCP config support via Hatch! ([330c683](https://github.com/CrackingShells/Hatch/commit/330c683))
* test(codex): add comprehensive CLI argument tests ([0e15301](https://github.com/CrackingShells/Hatch/commit/0e15301))
* test(codex): fix Omni model field name in conversion test ([21efc10](https://github.com/CrackingShells/Hatch/commit/21efc10))
* feat(codex): add CLI arguments for Codex ([88e81fe](https://github.com/CrackingShells/Hatch/commit/88e81fe))
* feat(codex): add MCPServerConfigCodex model and infrastructure ([061ae53](https://github.com/CrackingShells/Hatch/commit/061ae53))
* feat(codex): add tomli-w dependency for TOML support ([00b960f](https://github.com/CrackingShells/Hatch/commit/00b960f))
* feat(codex): implement CodexHostStrategy with TOML support ([4e55b34](https://github.com/CrackingShells/Hatch/commit/4e55b34))
* feat(mcp-models): map shared tool filtering flags to Codex ([b2e6103](https://github.com/CrackingShells/Hatch/commit/b2e6103))
* fix(backup): preserve original filename in backup creation ([c2dde46](https://github.com/CrackingShells/Hatch/commit/c2dde46))
* fix(codex): map http_headers to universal headers field ([7c5e2cb](https://github.com/CrackingShells/Hatch/commit/7c5e2cb))
* tests(codex): add comprehensive Codex host strategy test suite ([2858ba5](https://github.com/CrackingShells/Hatch/commit/2858ba5))

## <small>0.7.1-dev.1 (2025-12-15)</small>

* Merge branch 'feat/kiro-support' into dev ([d9c11ca](https://github.com/CrackingShells/Hatch/commit/d9c11ca))
* docs: add Kiro to supported MCP hosts across all documentation ([1b1dd1a](https://github.com/CrackingShells/Hatch/commit/1b1dd1a))
* docs(dev): enhance MCP host configuration extension guidance ([3bdae9c](https://github.com/CrackingShells/Hatch/commit/3bdae9c))
* fix: config path handling ([63efad7](https://github.com/CrackingShells/Hatch/commit/63efad7))
* test(kiro): add comprehensive backup integration tests ([65b4a29](https://github.com/CrackingShells/Hatch/commit/65b4a29))
* test(kiro): implement comprehensive test suite for Kiro MCP integration ([a55b48a](https://github.com/CrackingShells/Hatch/commit/a55b48a))
* test(kiro): implement test data infrastructure for Kiro MCP integration ([744219f](https://github.com/CrackingShells/Hatch/commit/744219f))
* feat(cli): add Kiro-specific arguments to mcp configure command ([23c1e9d](https://github.com/CrackingShells/Hatch/commit/23c1e9d))
* feat(kiro): add configuration file backup support ([49007dd](https://github.com/CrackingShells/Hatch/commit/49007dd))
* feat(mcp-host-config): add Kiro IDE support to model layer ([f8ede12](https://github.com/CrackingShells/Hatch/commit/f8ede12))
* feat(mcp-host-config): implement KiroHostStrategy for configuration management ([ab69e2a](https://github.com/CrackingShells/Hatch/commit/ab69e2a))

## 0.7.0 (2025-12-11)

* Merge pull request #42 from CrackingShells/dev ([be3a9a3](https://github.com/CrackingShells/Hatch/commit/be3a9a3)), closes [#42](https://github.com/CrackingShells/Hatch/issues/42)
* chore: add submodule `cracking-shells-playbook` ([c7fb36b](https://github.com/CrackingShells/Hatch/commit/c7fb36b))
* chore: clean remove __temp__/ and ignore it ([40b4a00](https://github.com/CrackingShells/Hatch/commit/40b4a00))
* chore: cleaning up old reports ([0119d0f](https://github.com/CrackingShells/Hatch/commit/0119d0f))
* chore: configure semantic-release for 0.x.x versioning behavior ([b04757a](https://github.com/CrackingShells/Hatch/commit/b04757a))
* chore: fix version numbers in changelog ([cfa6498](https://github.com/CrackingShells/Hatch/commit/cfa6498))
* chore(.gitignore): ignoring .augment and .github/instructions ([294ca04](https://github.com/CrackingShells/Hatch/commit/294ca04))
* chore(.gititnore): directory Laghari/ ([aa58720](https://github.com/CrackingShells/Hatch/commit/aa58720))
* chore(ci): clean semantic release commit message ([033ccc1](https://github.com/CrackingShells/Hatch/commit/033ccc1))
* chore(cli): remove useless --no-mcp-config flag ([7385763](https://github.com/CrackingShells/Hatch/commit/7385763))
* chore(release): 0.7.0-dev.1 ([700f190](https://github.com/CrackingShells/Hatch/commit/700f190))
* chore(release): 0.7.0-dev.10 ([4947480](https://github.com/CrackingShells/Hatch/commit/4947480))
* chore(release): 0.7.0-dev.11 ([d20de17](https://github.com/CrackingShells/Hatch/commit/d20de17))
* chore(release): 0.7.0-dev.12 ([09b7bcb](https://github.com/CrackingShells/Hatch/commit/09b7bcb))
* chore(release): 0.7.0-dev.13 ([0d94e4c](https://github.com/CrackingShells/Hatch/commit/0d94e4c))
* chore(release): 0.7.0-dev.2 ([a7bea4b](https://github.com/CrackingShells/Hatch/commit/a7bea4b))
* chore(release): 0.7.0-dev.3 ([28313b2](https://github.com/CrackingShells/Hatch/commit/28313b2))
* chore(release): 0.7.0-dev.4 ([c04984f](https://github.com/CrackingShells/Hatch/commit/c04984f))
* chore(release): 0.7.0-dev.5 ([66724ca](https://github.com/CrackingShells/Hatch/commit/66724ca))
* chore(release): 0.7.0-dev.6 ([321d2f1](https://github.com/CrackingShells/Hatch/commit/321d2f1))
* chore(release): 0.7.0-dev.7 ([35e25d8](https://github.com/CrackingShells/Hatch/commit/35e25d8))
* chore(release): 0.7.0-dev.8 ([72ff2be](https://github.com/CrackingShells/Hatch/commit/72ff2be))
* chore(release): 0.7.0-dev.9 ([dda6513](https://github.com/CrackingShells/Hatch/commit/dda6513))
* fix: backup system filename format ([f7af78a](https://github.com/CrackingShells/Hatch/commit/f7af78a))
* fix: config backup restore system ([981ff0c](https://github.com/CrackingShells/Hatch/commit/981ff0c))
* fix: correct report display logic to exclude unset fields ([478c655](https://github.com/CrackingShells/Hatch/commit/478c655))
* fix: implement environment-specific Python executable path resolution ([6119fe2](https://github.com/CrackingShells/Hatch/commit/6119fe2))
* fix: replace blocking input() with TTY-aware request_confirmation ([84caa7c](https://github.com/CrackingShells/Hatch/commit/84caa7c))
* fix: resolve all MCP CLI test failures achieving 100% pass rate ([e355bd7](https://github.com/CrackingShells/Hatch/commit/e355bd7))
* fix: resolve configuration file corruption and data loss issues ([55efeaa](https://github.com/CrackingShells/Hatch/commit/55efeaa))
* fix: resolve non-TTY environment blocking in request_confirmation ([799e1fa](https://github.com/CrackingShells/Hatch/commit/799e1fa))
* fix: use the FastMCP instance and not HatchMCP ([7179d31](https://github.com/CrackingShells/Hatch/commit/7179d31))
* fix(ci): Discord notification image URLs to use raw GitHub content ([0b8ce7c](https://github.com/CrackingShells/Hatch/commit/0b8ce7c))
* fix(ci): Discord pre-release notification should happen when on `dev` ([505ad2b](https://github.com/CrackingShells/Hatch/commit/505ad2b))
* fix(ci): plugin definition structure ([a5ed541](https://github.com/CrackingShells/Hatch/commit/a5ed541))
* fix(ci): using custom `@artessan-devs/sr-uv-plugin` ([fa47900](https://github.com/CrackingShells/Hatch/commit/fa47900))
* fix(claude-code): user-wide config file of the mcp ([ba5a02a](https://github.com/CrackingShells/Hatch/commit/ba5a02a))
* fix(cli): allow --http-url as standalone option for Gemini ([49e91bc](https://github.com/CrackingShells/Hatch/commit/49e91bc))
* fix(cli): enable partial configuration updates for existing MCP servers ([d545e90](https://github.com/CrackingShells/Hatch/commit/d545e90))
* fix(cli): implement shlex.split() for --args parsing ([a7e21d2](https://github.com/CrackingShells/Hatch/commit/a7e21d2))
* fix(cli): mcp host configuration when using paths to hatch pkgs ([902fa8a](https://github.com/CrackingShells/Hatch/commit/902fa8a))
* fix(cli): pass in expected mcp server configuration ([17d1cc3](https://github.com/CrackingShells/Hatch/commit/17d1cc3))
* fix(cli): resolve argparse naming conflict ([44d6a73](https://github.com/CrackingShells/Hatch/commit/44d6a73))
* fix(cli): resolve critical UnboundLocalError in hatch package add ([bdfa4c5](https://github.com/CrackingShells/Hatch/commit/bdfa4c5))
* fix(cli): string value usage ([aae1e85](https://github.com/CrackingShells/Hatch/commit/aae1e85))
* fix(deps): add pydantic dep ([bfa4aed](https://github.com/CrackingShells/Hatch/commit/bfa4aed))
* fix(dev): overwrite server config in mcp host rather than merging ([ce6ecc6](https://github.com/CrackingShells/Hatch/commit/ce6ecc6))
* fix(dev): remove host configuration ([6c5bc07](https://github.com/CrackingShells/Hatch/commit/6c5bc07))
* fix(docs): describe actual commit policy ([fee6da4](https://github.com/CrackingShells/Hatch/commit/fee6da4))
* fix(docs): repair all broken links ([e911324](https://github.com/CrackingShells/Hatch/commit/e911324))
* fix(docs): Tutorial 04-01 ([e855749](https://github.com/CrackingShells/Hatch/commit/e855749))
* fix(host): configuration cleanup after package and environment removal ([2824de7](https://github.com/CrackingShells/Hatch/commit/2824de7))
* fix(host): multi-environment mcp configuration conflict resolution ([1eb86e4](https://github.com/CrackingShells/Hatch/commit/1eb86e4))
* fix(lmstudio): user-wide config file of the mcp ([58b7613](https://github.com/CrackingShells/Hatch/commit/58b7613))
* fix(mcp): add Claude Desktop transport validation ([dede78e](https://github.com/CrackingShells/Hatch/commit/dede78e))
* fix(mcp): clear type field during transport switching ([1933351](https://github.com/CrackingShells/Hatch/commit/1933351))
* fix(mcp): remove incorrect absolute path validation for Claude Desktop ([50345a3](https://github.com/CrackingShells/Hatch/commit/50345a3))
* fix(pypi-deploy): remove direct dependencies ([2fc9313](https://github.com/CrackingShells/Hatch/commit/2fc9313))
* fix(pypi-deploy): wrong project name ([3957c75](https://github.com/CrackingShells/Hatch/commit/3957c75))
* fix(serialization): explicit model dump of server configuration ([fa273a4](https://github.com/CrackingShells/Hatch/commit/fa273a4))
* fix(test): function signatures and environment variable interference ([04838bc](https://github.com/CrackingShells/Hatch/commit/04838bc))
* fix(test): resolve failing integration tests with proper error handling ([5638299](https://github.com/CrackingShells/Hatch/commit/5638299))
* fix(tests): add missing mock ([1774610](https://github.com/CrackingShells/Hatch/commit/1774610))
* fix(tests): correct dependency dummy metadata extraction ([cbbdf40](https://github.com/CrackingShells/Hatch/commit/cbbdf40))
* fix(tests): update simple_dep_pkg to use local base_pkg ([f21ec7d](https://github.com/CrackingShells/Hatch/commit/f21ec7d))
* fix(vscode): set mcp configure to user-wide by default ([a688f52](https://github.com/CrackingShells/Hatch/commit/a688f52))
* fix(vscode): update configuration format from settings.json to mcp.json ([d08a202](https://github.com/CrackingShells/Hatch/commit/d08a202))
* fix(workaround): relax Pydantic data model constraint ([16c7990](https://github.com/CrackingShells/Hatch/commit/16c7990))
* docs: add --version flag documentation and installation verification ([724c957](https://github.com/CrackingShells/Hatch/commit/724c957))
* docs: add comprehensive MCP host configuration documentation ([e188c90](https://github.com/CrackingShells/Hatch/commit/e188c90))
* docs: add MCP backup system architecture documentation ([de7d16a](https://github.com/CrackingShells/Hatch/commit/de7d16a))
* docs: consolidate MCP/ subdirectory into MCPHostConfiguration.md ([3d5d11e](https://github.com/CrackingShells/Hatch/commit/3d5d11e))
* docs: CONTRIBUTING becomes `how_to_contribute.md` ([e10c236](https://github.com/CrackingShells/Hatch/commit/e10c236))
* docs: fix CLI reference documentation accuracy ([6d8c322](https://github.com/CrackingShells/Hatch/commit/6d8c322))
* docs: fix critical CLI command inaccuracies across documentation ([8ca57c3](https://github.com/CrackingShells/Hatch/commit/8ca57c3))
* docs: fix MCP host configuration dev guide ([0813ee2](https://github.com/CrackingShells/Hatch/commit/0813ee2))
* docs: minor legacy typos ([c48be5c](https://github.com/CrackingShells/Hatch/commit/c48be5c))
* docs: rewrite MCP host configuration ([b3597a8](https://github.com/CrackingShells/Hatch/commit/b3597a8))
* docs: update CLI reference for environment-scoped list hosts ([b2e5a80](https://github.com/CrackingShells/Hatch/commit/b2e5a80))
* docs: update CLI reference for MCP host configuration integration ([5a98b64](https://github.com/CrackingShells/Hatch/commit/5a98b64))
* docs: update CLIReference ([fb30d37](https://github.com/CrackingShells/Hatch/commit/fb30d37))
* docs: update cross-references following corrected alignment strategy ([79086a0](https://github.com/CrackingShells/Hatch/commit/79086a0))
* docs: update release policy for new CI/CD architecture ([a444c65](https://github.com/CrackingShells/Hatch/commit/a444c65))
* docs(cli): update CLI reference for parameter naming changes ([3d0a7a7](https://github.com/CrackingShells/Hatch/commit/3d0a7a7))
* docs(fix): release policy ([d326328](https://github.com/CrackingShells/Hatch/commit/d326328))
* docs(mcp): add comprehensive synchronization command documentation ([dab37fd](https://github.com/CrackingShells/Hatch/commit/dab37fd))
* docs(mcp): add user guide for direct management commands ([456971c](https://github.com/CrackingShells/Hatch/commit/456971c))
* docs(mcp): correct command examples and enhance configuration guidance ([edcca56](https://github.com/CrackingShells/Hatch/commit/edcca56))
* docs(mcp): streamline architecture documentation ([5b6ab9e](https://github.com/CrackingShells/Hatch/commit/5b6ab9e))
* docs(README): rewrite ([31ce6f9](https://github.com/CrackingShells/Hatch/commit/31ce6f9))
* docs(README): updating ([3b1cbd3](https://github.com/CrackingShells/Hatch/commit/3b1cbd3))
* docs(tutorials): update MCP host configuration tutorial content ([c06378f](https://github.com/CrackingShells/Hatch/commit/c06378f))
* docs(user): remove advanced synchronization tutorial step ([390ddff](https://github.com/CrackingShells/Hatch/commit/390ddff))
* docs(user): update tutorial on mcp host configuration ([8137957](https://github.com/CrackingShells/Hatch/commit/8137957))
* docs(users): remove low impact `CICDIntegration.md` ([27aafe0](https://github.com/CrackingShells/Hatch/commit/27aafe0))
* ci: add `artessan-devs/sr-uv-plugin` to semantic release ([7f5c7d2](https://github.com/CrackingShells/Hatch/commit/7f5c7d2))
* ci: add Discord notifications for releases and pre-releases ([ea6ecb2](https://github.com/CrackingShells/Hatch/commit/ea6ecb2))
* ci: add pypi publication ([a86fa7c](https://github.com/CrackingShells/Hatch/commit/a86fa7c))
* ci: avoid publishing release on commit `fix(docs)` ([fb62e0a](https://github.com/CrackingShells/Hatch/commit/fb62e0a))
* ci: refactor CI/CD pipeline into separate workflows ([8342999](https://github.com/CrackingShells/Hatch/commit/8342999))
* style: apply ruff to `template_generator.py` ([638a9dd](https://github.com/CrackingShells/Hatch/commit/638a9dd))
* style: json formating of the `.releaserc.json` ([681a922](https://github.com/CrackingShells/Hatch/commit/681a922))
* refactor: directory name ([c5858ff](https://github.com/CrackingShells/Hatch/commit/c5858ff))
* refactor: remove outdated __version__ from hatch/__init__.py ([4d06b40](https://github.com/CrackingShells/Hatch/commit/4d06b40))
* refactor(cli): rename --headers to --header for consistency ([5d84755](https://github.com/CrackingShells/Hatch/commit/5d84755))
* refactor(cli): rename --inputs to --input for consistency ([0807712](https://github.com/CrackingShells/Hatch/commit/0807712))
* refactor(cli): replace --env with --env-var in mcp configure ([945f66b](https://github.com/CrackingShells/Hatch/commit/945f66b))
* refactor(test): mark tests taking around 30 secs as slow ([535843c](https://github.com/CrackingShells/Hatch/commit/535843c))
* feat: add --version flag to CLI argument parser ([c3410c3](https://github.com/CrackingShells/Hatch/commit/c3410c3))
* feat: add decorator registration for new MCP host configs ([61681be](https://github.com/CrackingShells/Hatch/commit/61681be))
* feat: add get_server_config method for server existence detection ([7b53e42](https://github.com/CrackingShells/Hatch/commit/7b53e42))
* feat: add host-specific CLI arguments for MCP configure command ([40faabb](https://github.com/CrackingShells/Hatch/commit/40faabb))
* feat: add host-specific MCP configuration models with type field ([655cf0a](https://github.com/CrackingShells/Hatch/commit/655cf0a))
* feat: add user feedback reporting system for MCP configuration ([fa8fa42](https://github.com/CrackingShells/Hatch/commit/fa8fa42))
* feat: add user feedback reporting to package add/sync commands ([f244c61](https://github.com/CrackingShells/Hatch/commit/f244c61))
* feat: enhance package management with MCP host configuration integration ([7da69aa](https://github.com/CrackingShells/Hatch/commit/7da69aa))
* feat: implement ALL host-specific CLI arguments with new reporting ([6726bbb](https://github.com/CrackingShells/Hatch/commit/6726bbb))
* feat: implement comprehensive host configuration tracking system ([4e496bc](https://github.com/CrackingShells/Hatch/commit/4e496bc))
* feat: implement consolidated MCPServerConfig Pydantic model ([e984a82](https://github.com/CrackingShells/Hatch/commit/e984a82))
* feat: implement decorator-based strategy registration system ([b424520](https://github.com/CrackingShells/Hatch/commit/b424520))
* feat: implement environment-scoped list hosts command ([d098b0b](https://github.com/CrackingShells/Hatch/commit/d098b0b))
* feat: implement host strategy classes with inheritance architecture ([1e8d95b](https://github.com/CrackingShells/Hatch/commit/1e8d95b))
* feat: implement MCP backup management commands (Phase 3d) ([ee04223](https://github.com/CrackingShells/Hatch/commit/ee04223))
* feat: implement MCP host configuration backup system ([de661e2](https://github.com/CrackingShells/Hatch/commit/de661e2))
* feat: implement MCP host discovery and listing commands (Phase 3c) ([f8fdbe9](https://github.com/CrackingShells/Hatch/commit/f8fdbe9))
* feat: implement package-MCP integration with existing APIs ([f4dd2fc](https://github.com/CrackingShells/Hatch/commit/f4dd2fc))
* feat: implement partial update merge logic in CLI handler ([4268d4e](https://github.com/CrackingShells/Hatch/commit/4268d4e))
* feat: integrate Pydantic model hierarchy into CLI handlers ([d59fc6a](https://github.com/CrackingShells/Hatch/commit/d59fc6a))
* feat(cli): enhance mcp configure command argument structure ([7d385e6](https://github.com/CrackingShells/Hatch/commit/7d385e6))
* feat(cli): implement hatch mcp sync command with advanced options ([80f67a1](https://github.com/CrackingShells/Hatch/commit/80f67a1))
* feat(cli): implement object-action pattern for MCP remove commands ([b172ab4](https://github.com/CrackingShells/Hatch/commit/b172ab4))
* feat(mcp): add host configuration removal functionality ([ca82163](https://github.com/CrackingShells/Hatch/commit/ca82163))
* feat(mcp): implement advanced synchronization backend ([9ed6ec6](https://github.com/CrackingShells/Hatch/commit/9ed6ec6))
* feat(mcp): implement Gemini dual-transport validation ([f715df1](https://github.com/CrackingShells/Hatch/commit/f715df1))
* feat(tutorials): add complete MCP Host Configuration tutorial series ([a0a5ba4](https://github.com/CrackingShells/Hatch/commit/a0a5ba4))
* test: add atomic file operations and backup-aware operation tests ([aac323e](https://github.com/CrackingShells/Hatch/commit/aac323e))
* test: add CLI integration tests for MCP host configuration ([a1e3c21](https://github.com/CrackingShells/Hatch/commit/a1e3c21))
* test: add comprehensive MCPHostConfigBackupManager tests ([0bfeecf](https://github.com/CrackingShells/Hatch/commit/0bfeecf))
* test: add comprehensive MCPServerConfig model validation tests ([391f2b9](https://github.com/CrackingShells/Hatch/commit/391f2b9))
* test: add comprehensive test suite for environment-scoped commands ([077c532](https://github.com/CrackingShells/Hatch/commit/077c532))
* test: add comprehensive test suite for partial configuration updates ([47dd21e](https://github.com/CrackingShells/Hatch/commit/47dd21e))
* test: add comprehensive tests for MCP configuration models ([0265d48](https://github.com/CrackingShells/Hatch/commit/0265d48))
* test: add configuration manager integration tests ([502ab4c](https://github.com/CrackingShells/Hatch/commit/502ab4c))
* test: add decorator-based strategy registration validation tests ([ff80500](https://github.com/CrackingShells/Hatch/commit/ff80500))
* test: add environment integration validation tests ([99302fe](https://github.com/CrackingShells/Hatch/commit/99302fe))
* test: add integration and performance tests for backup system ([7b6a261](https://github.com/CrackingShells/Hatch/commit/7b6a261))
* test: add MCP backup test infrastructure and data utilities ([ed5cd35](https://github.com/CrackingShells/Hatch/commit/ed5cd35))
* test: add tests for user feedback reporting ([d8076e2](https://github.com/CrackingShells/Hatch/commit/d8076e2))
* test: add version command test suite ([ac9919b](https://github.com/CrackingShells/Hatch/commit/ac9919b))
* test: extend test data infrastructure for MCP host configuration ([688b4ed](https://github.com/CrackingShells/Hatch/commit/688b4ed))
* test(env): enhance environment cleanup to prevent debris accumulation ([b0c9c7f](https://github.com/CrackingShells/Hatch/commit/b0c9c7f))
* test(mcp): add comprehensive test coverage for new remove commands ([73f39f2](https://github.com/CrackingShells/Hatch/commit/73f39f2))
* test(mcp): add comprehensive test suite for sync functionality ([969c793](https://github.com/CrackingShells/Hatch/commit/969c793))


### Breaking change

* Code that relied on hatch.__version__ will need to use
importlib.metadata.version('hatch') instead.

Related to: Phase 1 analysis (version_command_analysis_v1.md)

## [0.7.0-dev.13](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.12...v0.7.0-dev.13) (2025-12-11)


### Bug Fixes

* **ci:** Discord notification image URLs to use raw GitHub content ([847dd1c](https://github.com/CrackingShells/Hatch/commit/847dd1c8e8269a9a2c70ddecf95e10d7943c9596))


### Documentation

* **README:** rewrite ([b05f8a5](https://github.com/CrackingShells/Hatch/commit/b05f8a5d7510aaf60c692ddb36ee5e7b28dc8077))
* update release policy for new CI/CD architecture ([3df2ae2](https://github.com/CrackingShells/Hatch/commit/3df2ae2a1235223afd6e28b96c29c9c09f22eea1))

## [0.7.0-dev.12](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.11...v0.7.0-dev.12) (2025-12-10)


### Documentation

* fix CLI reference documentation accuracy ([61458d3](https://github.com/CrackingShells/Hatch/commit/61458d3d18de7489f874562e288d69cdaaf15969))
* fix MCP host configuration extension guide with critical corrections ([1676af0](https://github.com/CrackingShells/Hatch/commit/1676af003ec41a65f23a012d2427b2a98d892b77))
* **README:** Updating ([fbcbd14](https://github.com/CrackingShells/Hatch/commit/fbcbd1480e6272837770caeec92d8bae62f06f45))

## [0.7.0-dev.11](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.10...v0.7.0-dev.11) (2025-12-07)


### Bug Fixes

* **pypi-deploy:** wrong project name ([f94df05](https://github.com/CrackingShells/Hatch/commit/f94df05eef37d6e4b9af818ba66a69be9aa7ff6f))

## [0.7.0-dev.10](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.9...v0.7.0-dev.10) (2025-12-07)


### Bug Fixes

* **pypi-deploy:** remove direct dependencies ([0875cf8](https://github.com/CrackingShells/Hatch/commit/0875cf816e97d5cb3b573f6ba95a802d236e8145))

## [0.7.0-dev.9](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.8...v0.7.0-dev.9) (2025-12-02)


### Bug Fixes

* **mcp:** remove incorrect absolute path validation for Claude Desktop ([1029991](https://github.com/CrackingShells/Hatch/commit/1029991fb7897647d8214ccf10b12e41c3b723d8))

## [0.7.0-dev.8](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.7...v0.7.0-dev.8) (2025-11-24)


### Bug Fixes

* **docs:** describe actual commit policy ([d42777e](https://github.com/CrackingShells/Hatch/commit/d42777eb2bdfefdfcfdce82d1b655f2764424ad5))
* **docs:** repair all broken links ([7378ebb](https://github.com/CrackingShells/Hatch/commit/7378ebbdb52a3b802959608e23f511389e07cddf))


### Documentation

* CONTRIBUTING becomes `how_to_contribute.md` ([e2b1b13](https://github.com/CrackingShells/Hatch/commit/e2b1b1327f506f8bf59776026f709deb12082f2d))
* **fix:** release policy ([8a6c5a0](https://github.com/CrackingShells/Hatch/commit/8a6c5a0068cfbb9ce5377fa7f7b4552db28e2ba4))
* update CLIReference ([fa801e9](https://github.com/CrackingShells/Hatch/commit/fa801e90215de729f4e036b04c5cda2f0058823b))
* **user:** remove advanced synchronization tutorial step ([bd0cbff](https://github.com/CrackingShells/Hatch/commit/bd0cbff3ff8a985a8aacf2303960b1a0e49f94e5))
* **users:** remove low impact `CICDIntegration.md` ([996e99d](https://github.com/CrackingShells/Hatch/commit/996e99d9bf73c6889519456f5a9a9a9abd6f6c1d))
* **user:** update tutorial on mcp host configuration ([6033841](https://github.com/CrackingShells/Hatch/commit/6033841554ce2f8955d9981cc686380cd3c72cb3))

## [0.7.0-dev.7](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.6...v0.7.0-dev.7) (2025-11-18)


### Bug Fixes

* **cli:** enable partial configuration updates for existing MCP servers ([edaa4b5](https://github.com/CrackingShells/Hatch/commit/edaa4b5873921d1f6bbd0a3b5e536a129c2d0403))

## [0.7.0-dev.6](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.5...v0.7.0-dev.6) (2025-10-30)


### Features

* add get_server_config method for server existence detection ([0746c7c](https://github.com/CrackingShells/Hatch/commit/0746c7c778eb47908818463a330d78e2ead3dc77))
* implement partial update merge logic in CLI handler ([76cae67](https://github.com/CrackingShells/Hatch/commit/76cae6794018b6996189cab690149360b49c8ed6))
* **mcp:** implement Gemini dual-transport validation ([99027e8](https://github.com/CrackingShells/Hatch/commit/99027e8e9aa37c54b2ce1b2a27d5411836882f48))


### Bug Fixes

* **cli:** allow --http-url as standalone option for Gemini ([1e2a51d](https://github.com/CrackingShells/Hatch/commit/1e2a51d8c0265f2ff84349b821e16115aafbae1d))
* **cli:** implement shlex.split() for --args parsing ([3c67a92](https://github.com/CrackingShells/Hatch/commit/3c67a9277787fe432b9d7d111d217a72abaaedbf))
* **mcp:** add Claude Desktop transport validation ([b259a37](https://github.com/CrackingShells/Hatch/commit/b259a37aea613d5cc9111c8532b1a799c362add5))
* **mcp:** clear type field during transport switching ([d39eedf](https://github.com/CrackingShells/Hatch/commit/d39eedf5e669a90f29ce4aad05434aee96b56d3a))


### Documentation

* **cli:** update CLI reference for parameter naming changes ([52010fa](https://github.com/CrackingShells/Hatch/commit/52010fa0cb7c62517e55bda5df11c4a4ce0e45c4))


### Code Refactoring

* **cli:** rename --headers to --header for consistency ([a1d648d](https://github.com/CrackingShells/Hatch/commit/a1d648d1dbd8cbbefdc1130f25f246494069c76c))
* **cli:** rename --inputs to --input for consistency ([905ed39](https://github.com/CrackingShells/Hatch/commit/905ed39c165c926eed8bcbc0583d207645f37160))

## [0.7.0-dev.5](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.4...v0.7.0-dev.5) (2025-10-13)


### Features

* add host-specific CLI arguments for MCP configure command ([a0e840d](https://github.com/CrackingShells/Hatch/commit/a0e840d00db94018fed6f8e22c6f39985b5a7506))
* add host-specific MCP configuration models with type field ([63e78ed](https://github.com/CrackingShells/Hatch/commit/63e78ede4cdad66f8f4a5c1682835e55232f6f26))
* add user feedback reporting system for MCP configuration ([b15d48a](https://github.com/CrackingShells/Hatch/commit/b15d48a95f62dca6d66b10ee9a64b9015d62526e))
* add user feedback reporting to package add/sync commands ([a6ad932](https://github.com/CrackingShells/Hatch/commit/a6ad932b894f519d71472b0032c7f19b50979177))
* implement ALL host-specific CLI arguments with new reporting ([75943b9](https://github.com/CrackingShells/Hatch/commit/75943b98454c35f196e01f1a3fa0b1ed995ab940))
* integrate Pydantic model hierarchy into CLI handlers ([eca730a](https://github.com/CrackingShells/Hatch/commit/eca730a6b632eab7dd40379eeed67f8f5f390297))


### Bug Fixes

* **cli:** resolve argparse naming conflict ([83ab933](https://github.com/CrackingShells/Hatch/commit/83ab933e12a8d8051538eac9812c8f1a3ef3b64d))
* correct report display logic to exclude unset fields ([5ba2076](https://github.com/CrackingShells/Hatch/commit/5ba2076ea0df6dfb21536dddee712089fd2e18bd))
* **tests:** add missing mock ([78cd421](https://github.com/CrackingShells/Hatch/commit/78cd4215960b3270ed2f9767dc96bd1522a03f45))
* **tests:** correct dependency dummy metadata extraction ([9573e45](https://github.com/CrackingShells/Hatch/commit/9573e452be9ff8b1669ff5e1d85bf40aff29ae29))
* **tests:** update simple_dep_pkg to use local base_pkg ([b1bf8bd](https://github.com/CrackingShells/Hatch/commit/b1bf8bddcdc7c00df082a55b71db39de5c9a7954))


### Documentation

* update CLI reference for MCP host configuration integration ([ef1b7ca](https://github.com/CrackingShells/Hatch/commit/ef1b7ca8765dd8d983f634d4789a37d9855b443c))

## [0.7.0-dev.4](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.3...v0.7.0-dev.4) (2025-10-02)


### ⚠ BREAKING CHANGES

* Code that relied on hatch.__version__ will need to use
importlib.metadata.version('hatch') instead.

Related to: Phase 1 analysis (version_command_analysis_v1.md)

### Features

* add --version flag to CLI argument parser ([d1a0e2d](https://github.com/CrackingShells/Hatch/commit/d1a0e2dfb5963724294b3e0c84e0b7f96aefbe61))


### Documentation

* add --version flag documentation and installation verification ([ac326e0](https://github.com/CrackingShells/Hatch/commit/ac326e0a5bed84f9ce8d38976cd9dbfafdc24685))


### Code Refactoring

* remove outdated __version__ from hatch/__init__.py ([9f0aad3](https://github.com/CrackingShells/Hatch/commit/9f0aad3684a794019aa1b6033ac4b9645a92d6af))

## [0.7.0-dev.3](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.2...v0.7.0-dev.3) (2025-10-01)


### Bug Fixes

* **claude-code:** user-wide config file of the mcp ([4b5d2d9](https://github.com/CrackingShells/Hatch/commit/4b5d2d9981135e747a2f51651a85aef47ad60292))
* **lmstudio:** user-wide config file of the mcp ([5035b88](https://github.com/CrackingShells/Hatch/commit/5035b88eb916cce498a82dedbb1552c0d052b6c6))

## [0.7.0-dev.2](https://github.com/CrackingShells/Hatch/compare/v0.7.0-dev.1...v0.7.0-dev.2) (2025-09-29)


### Features

* **cli:** enhance mcp configure command argument structure ([bc89077](https://github.com/CrackingShells/Hatch/commit/bc89077bacb668b3d3b7899bddbd6abea6a1f37b))
* implement environment-scoped list hosts command ([06daf51](https://github.com/CrackingShells/Hatch/commit/06daf51de179c01f09d343193ef69edf861e3e55))
* **tutorials:** add complete MCP Host Configuration tutorial series ([00bad1c](https://github.com/CrackingShells/Hatch/commit/00bad1cc51483b254353f94f34db27e1d208d11e))


### Bug Fixes

* **ci:** Discord pre-release notification should happen when on `dev` ([c41c027](https://github.com/CrackingShells/Hatch/commit/c41c027d2b4f9006239cd122c3275f0d3880bc78))
* **cli:** mcp host configuration would failed when using paths to add hatch packages ([701c93c](https://github.com/CrackingShells/Hatch/commit/701c93c6549c702d0ce6c880c7983446c7ba7bd2))
* **cli:** pass in expected mcp server configuration ([1f2b7cb](https://github.com/CrackingShells/Hatch/commit/1f2b7cb25fbce2897f4edfa29f3e81787e94e7ef))
* **cli:** resolve critical UnboundLocalError in hatch package add command ([f03b472](https://github.com/CrackingShells/Hatch/commit/f03b472206542f45c470d8b7356d73f3fd9a6f80))
* **dev:** overwrite server configuration in mcp host configs rather than merging ([324ec69](https://github.com/CrackingShells/Hatch/commit/324ec69e8991429feffa49f27418269680e3f8df))
* **dev:** remove host configuration only clears MCP servers configuration ([0f5b943](https://github.com/CrackingShells/Hatch/commit/0f5b943adc5203fa21c940d28d8ee11b71b86df2))
* **docs:** Tutorial 04-01 ([86d17b6](https://github.com/CrackingShells/Hatch/commit/86d17b6a7d5a79625b36cd24d5a179f8c104e0f3))
* **host:** configuration cleanup after package and environment removal ([96d9e3e](https://github.com/CrackingShells/Hatch/commit/96d9e3ef9b14b33a8b5cb569fe8305f5e94508be))
* **host:** multi-environment mcp configuration conflict resolution ([a3f46be](https://github.com/CrackingShells/Hatch/commit/a3f46be11b06f2da50dc22723a75ac786caeb572))
* **serialization:** explicit model dump of server configuration ([1019953](https://github.com/CrackingShells/Hatch/commit/1019953e69898c870cf240c85947fa927dafdf39))
* **test:** function signatures and environment variable interference ([9c7a738](https://github.com/CrackingShells/Hatch/commit/9c7a738a1ca6f02097796054b5b22da858e813ef))
* **vscode:** replace broken workspace-only strategy with user-wide settings support ([3c452d4](https://github.com/CrackingShells/Hatch/commit/3c452d4bcaabd9cdd3944b543036930baf04b1e0))
* **vscode:** update configuration format from settings.json to mcp.json ([7cc0d0a](https://github.com/CrackingShells/Hatch/commit/7cc0d0ad4cbdef85c5cbe7a719659540a8410512))
* **workaround:** relax Pydantic data model constraint ([5820ab1](https://github.com/CrackingShells/Hatch/commit/5820ab17c287f60c5d3c0c91f8badc7185eb9580))


### Documentation

* consolidate MCP/ subdirectory into MCPHostConfiguration.md ([f2e58c5](https://github.com/CrackingShells/Hatch/commit/f2e58c5e0efba28a9286e64b550bb988ced84620))
* fix critical CLI command inaccuracies across documentation ([f6fffe7](https://github.com/CrackingShells/Hatch/commit/f6fffe7274134d47d0782262e1e6ac89f5943ffb))
* **mcp:** correct command examples and enhance configuration guidance ([163a1ed](https://github.com/CrackingShells/Hatch/commit/163a1ed8c36cc4d0d205920c5ae2d14b93e1d7dd))
* minor legacy typos ([bc5df04](https://github.com/CrackingShells/Hatch/commit/bc5df04a40b97bdaa203bf03a4286858a7988b7d))
* **tutorials:** update MCP host configuration tutorial content ([9cef886](https://github.com/CrackingShells/Hatch/commit/9cef886f1a6cc04884b960aec71904bd0ca0a788))
* update CLI reference for environment-scoped list hosts ([7838781](https://github.com/CrackingShells/Hatch/commit/7838781809219da065ee8491a6b112f9a484ab76))
* update cross-references following corrected alignment strategy ([3b3eeea](https://github.com/CrackingShells/Hatch/commit/3b3eeea3e91d677296ddaae1727b2ceca835feaa))


### Code Refactoring

* **cli:** replace --env with --env-var for environment variables in mcp configure ([82ddabd](https://github.com/CrackingShells/Hatch/commit/82ddabd042c1163326deb706c71699634c5bc095))

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
