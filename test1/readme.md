pyenv install 3.10.13
mkdir my_project && cd my_project
pyenv virtualenv 3.10.13 my_project-env
pyenv local my_project-env
python --version  # Should be 3.10.13
