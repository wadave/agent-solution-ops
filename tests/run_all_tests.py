# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Master script to run all tests."""
import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import integration tests
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from integration import test_deployed_hosting_agent


async def main():
    """Run all primary integration test suites sequentially."""
    print("="*80)
    print("STARTING A2A INTEGRATION TESTS")
    print("="*80)

    # Track overall success
    all_success = True

    # 1. Test ADK Hosting Agent
    try:
        success = await test_deployed_hosting_agent.main()
        if not success:
            all_success = False
    except Exception as e:
        print(f"\n✗ Error running hosting agent tests: {e}")
        all_success = False

    # Summary
    print("\n" + "="*80)
    if all_success:
        print("✓ ALL TEST SUITES PASSED!")
        sys.exit(0)
    else:
        print("✗ SOME TEST SUITES FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
