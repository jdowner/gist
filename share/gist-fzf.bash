#!/bin/bash

# This function uses fzf to fuzzy match the output from 'gist list' in order to
# enter a gist ID to commands that required IDs.
__gist() {
  local curr=${COMP_WORDS[COMP_CWORD]}
  local cmd=${COMP_WORDS[1]}

  COMPREPLY=()

  case ${cmd} in
    edit|description|archive|files|content|clone|info)
      if (( ${COMP_CWORD} == 2 )); then
        tput smcup
        COMPREPLY=( $( gist list | fzf | cut -d" " -f1 ) )
        tput rmcup
      fi
      ;;
    delete)
      tput smcup
      COMPREPLY=( $( gist list | fzf | cut -d" " -f1 ) )
      tput rmcup
      ;;
    create|list|fork)
      ;;
    *)
      COMPREPLY=( $(compgen -W "edit description delete create fork archive files content clone list info" -- $curr) )
      ;;
  esac

}

complete -F __gist gist
