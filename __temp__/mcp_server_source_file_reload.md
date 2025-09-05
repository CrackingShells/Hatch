### `hatch package reload`

This is the default, it reloads **all** the *Hatch!* packages in the **current** *Hatch!* environment

### `hatch package reload --env <hatch_env_name>`

Reloads **all**the *Hatch!* packages in the *Hatch!* environment `<hatch_env_name>` irrespective of the current environment

### `hatch package reload --env <hatch_env_name> --all-envs`

Reloads **all**the *Hatch!* packages in **all** *Hatch!* environments irrespective of `<hatch_env_name>`

### `hatch package reload --pkg <hatch_pkg_name>`

Reloads the *Hatch!* package `<hatch_pkg_name>` in the current *Hatch!* environment

### `hatch package reload --pkg <hatch_pkg_name> --env <hatch_env_name>`

Reloads the *Hatch!* package `<hatch_pkg_name>` in the *Hatch!* environment `<hatch_env_name>`

### `hatch package reload --pkg <hatch_pkg_name> --env <hatch_env_name>　--all-envs`

Reloads the *Hatch!* package `<hatch_pkg_name>` in **all**  *Hatch!* environments irrespective of `<hatch_env_name>`

Finally, default behavior is to skip reinstalling the dependencies unless specified with a flag `--reload-deps`.
