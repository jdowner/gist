#!/bin/bash

__gist()
{
  local curr=${COMP_WORDS[COMP_CWORD]}
  COMPREPLY=( $(compgen -W "delete create archive files content clone list info" -- $curr) )
}

complete -F __gist gist
