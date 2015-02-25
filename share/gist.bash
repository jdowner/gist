#!/bin/bash

__gist() {
  local curr=${COMP_WORDS[COMP_CWORD]}
  local cmd=${COMP_WORDS[1]}

  COMPREPLY=()

  case ${cmd} in
    edit|description|delete|archive|files|content|clone|list|info|fork)
      ;;
    create)
      if (( ${COMP_CWORD} >= 2 )); then
        compopt -o filenames
        COMPREPLY=( $(compgen -f -- ${curr}) )
      fi
      ;;
    *)
      COMPREPLY=( $(compgen -W "edit description delete create fork archive files content clone list info" -- $curr) )
      ;;
  esac

}

complete -F __gist gist
