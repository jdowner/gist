#!/bin/bash

__gist() {
  local curr=${COMP_WORDS[COMP_CWORD]}
  local cmd=${COMP_WORDS[1]}

  COMPREPLY=()

  case ${cmd} in
    edit|delete|archive|files|content|clone|list|info)
      ;;
    create)
      if (( ${COMP_CWORD} >= 2 )); then
        compopt -o filenames
        COMPREPLY=( $(compgen -f -- ${curr}) )
      fi
      ;;
    *)
      COMPREPLY=( $(compgen -W "edit delete create archive files content clone list info" -- $curr) )
      ;;
  esac

}

complete -F __gist gist
