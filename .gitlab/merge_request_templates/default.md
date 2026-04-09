*Add your MR description here*

----------------

# Definition of Done

- [ ] **Unit testing:** I wrote unit tests for all public functions and made sure that I covered all possible scenarios. Where reasonable, I also wrote unit tests for internal functions. All tests run successfully.
- [ ] **Documentation:** I wrote docstrings for all public functions. The docstrings contain a general description of what the function does, a description of the arguments, the return value and exceptions that can be raised. I added an example to the docstrings for each function. I used the numpy docstring format and checked that the documentation is built successfully. 
- [ ] **Code style:** I followed the coding style guidelines using the internal `ruff` configuration. I only made exceptions to the coding style guidelines if absolutely necessary. I checked the code style using `ruff` and no rules were violated.
- [ ] **Commit messages:** I wrote all commit messages relevant for the changelog following the conventional commits specification. I verified that all relevant changes occur in the correct category in the changelog by building it using `git cliff`. I checked that the changelog doesn't contain any duplicates or unneccesary changes. Where needed, I edited the commit messages to match the Definition of Done. 
- [ ] **CI/CD:** I adapted the CI/CD pipeline where necessary and checked that all jobs run succesfully. The CI/CD pipeline includes building the package, building the documentation and running tests for all supported Python versions.
- [ ] **Github Workflows:** I adapted the Github workflows where necessary.
