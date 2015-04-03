#compdef gist

_arguments \
  '*:: :->subcmds' && return 0

local -a _first_arguments
_first_arguments=(
  'list:Print the list of your gists.'
  'edit:Edit the files in your gist.'
  'info:Print detailed information about the gist.'
  'fork:Create a fork of the gist.'
  'description:Update the description of the gist.'
  'files:Print the list of files in a gist.'
  'delete:Delete the gist from GitHub.'
  'archive:Download the gist and create a tarball.'
  'content:Print the contents of the gist to stdout.'
  'create:Create a new gist.'
  'clone:Clone the gist to a local repository.'
)

if (( CURRENT == 1 )); then
  _describe -t commands "gist subcommand" _first_arguments
  return
fi

case "$words[1]" in
  (create)
    _arguments \
      '--public[Create a public gist.]' \
      '--encrypt[Encrypt the gist.]' \
      ':description: :' \
      '*:: :_files'
  ;;
  (content)
    _arguments \
      '--decrypt[Decrypt the gist.]'
  ;;
esac
