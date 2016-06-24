#!/bin/bash
#
# Starts up an Aurora scheduler process.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


source /etc/sysconfig/aurora-scheduler

# Environment variables control the behavior of the Mesos scheduler driver (libmesos).
export GLOG_v LIBPROCESS_PORT LIBPROCESS_IP
export JAVA_OPTS="${JAVA_OPTS[*]}"

# Preferences Java 1.8 over any other Java version.
export PATH=/usr/lib/jvm/java-1.8.0/bin:${PATH}

exec /usr/lib/aurora/bin/aurora-scheduler "${AURORA_FLAGS[@]}"
