#!/usr/bin/env bash
#
#  Copyright Bradley Lowekamp
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0.txt
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

# This script takes a path as an argument to create a commit on the ENV:TARGET_BRANCH or "gh-pages" branch which sets
# the branch to match the contents for the provided path.

set -eu

target_branch=${TARGET_BRANCH:-"gh-pages"}


if [[ -n "${GITHUB_ACTOR+x}" ]]; then
    git config user.name "$GITHUB_ACTOR"
    git config user.email "${GITHUB_ACTOR}@bots.github.com"
fi



die()
{
  echo "Error: $@" 1>&2
  exit 1
}


usage()
{
  die "Usage: $0 path_to_branch"
}


if [[ ! -d "$1" ]] ; then
    echo "Argument is not a directory: $1" 1>&2
    usage
fi

branch_path="$(cd "$(dirname "$1")" && pwd)"
branch_path="$branch_path/$(basename "$1")"

toplevel_path=$( cd "$( dirname "$0" )" && git rev-parse --show-toplevel)
cd "$toplevel_path"


old_branch_sha=$(git rev-list -n 1 "$target_branch" )
echo "Current $target_branch change id: $old_branch_sha"

branch_temp_index="$toplevel_path/$target_branch.index"
rm -rf "$branch_temp_index"



new_tree=$(
  GIT_WORK_TREE="$branch_path" &&
  GIT_INDEX_FILE="$branch_temp_index" &&
  export GIT_WORK_TREE GIT_INDEX_FILE &&
  git add --all &&
  git write-tree
) || die "creating new tree failed"

rm -rf "$branch_temp_index"

if [[ -z $(git diff-tree "$new_tree" "$old_branch_sha") ]]; then
    echo "No changes to $target_branch branch."
    exit 0
fi


new_changeid=$(git commit-tree "$new_tree" -p "$old_branch_sha" -m "Automatic Update

$(date)")
echo "Updating $target_branch with $new_changeid..."
git update-ref refs/heads/$target_branch $new_changeid

