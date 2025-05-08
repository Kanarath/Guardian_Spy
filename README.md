# Guardian Spy 🛡️🕶️

**Version:** 0.1.0-alpha

**Guardian Spy is a CLI tool designed to assist OSINT practitioners in maintaining operational security (OPSEC) during their investigations by managing secure and isolated browsing sessions.**

It helps you prepare your environment, launch browsers with fresh temporary profiles, perform basic connection checks, and clean up traces after your session.

## Core Features (MVP & Planned)

*   **Isolated Browser Sessions:**
    *   Launch Firefox or Chrome/Chromium with a **new, temporary profile** that is deleted upon closing.
    *   (Planned) Option to use/manage **persistent isolated profiles** for longer-term investigations.
*   **OPSEC Checks:**
    *   Display current public IP address and basic geolocation.
    *   Show currently configured system DNS servers.
    *   (Planned) DNS leak testing.
    *   (Planned) User-Agent management/randomization reminders.
*   **Session Management:**
    *   Interactive CLI for session setup.
    *   (Planned) "Quick mode" for fast default startups.
    *   (Planned) Customizable bookmark sets for different investigation types.
*   **Cleanup:**
    *   Automatic deletion of temporary browser profiles.
    *   (Planned) Optional system-level cleanup (temp files, cache).
*   **Metadata Handling:**
    *   (Planned) Read and strip metadata from files.
*   **(Vision) Integration with Sock Spy:**
    *   (Planned) Ability to load data from Sock Spy profiles to inform session setup.

## Why Guardian Spy?

Maintaining OPSEC is crucial in OSINT to protect your identity, location, and the integrity of your investigation. Guardian Spy aims to simplify some of the common steps involved in setting up a cleaner, more isolated environment for online research, reducing the risk of accidental deanonymization or cross-contamination of digital footprints.

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/guardian-spy.git # Replace YOUR_USERNAME
cd guardian-spy

# 2. (Recommended) Create and activate a virtual environment
python -m venv venv
# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## This command will start Guardian Spy

```bash
python guardian_spy.py
```

## The next steps will be:

It will perform initial IP and DNS checks.
It will ask you to select a browser (Firefox or Chrome).
It will create a new temporary profile for the selected browser.
It will launch the browser with this temporary profile.
When you close the browser, Guardian Spy will detect this and automatically delete the temporary profile.

## Command-line options (Example for future):

```bash
python guardian_spy.py --browser chrome --quick
Use code with caution.
```

## Planned Features / Roadmap

Persistent Profile Management (create, list, load, delete).
Advanced Bookmark Set Management.
Robust DNS Leak Testing.
User-Agent selection/customization.
"Quick Mode" with pre-saved configurations.
System Cleanup Module (temp files, main browser cache).
Metadata Reader/Stripper module.
Configuration file for Guardian Spy settings.
Integration with "Sock Spy" for identity context.
Enhanced CLI (e.g., using python-inquirer or click).
Cross-platform testing and refinement (especially for browser paths and DNS).
Contributing
Contributions are welcome! If you have ideas, suggestions, or want to help with development, please:
Fork the repository.
Create a new branch for your feature or bug fix.
Make your changes.
Submit a pull request.
Please open an issue first to discuss any major changes.
License
This project is licensed under the GNU General Public License v3.0. See the LICENSE file for details.
Disclaimer
Guardian Spy is a tool to assist with OPSEC but does not guarantee complete anonymity or security. Always use it as part of a broader OPSEC strategy and understand the limitations of any single tool. The user is responsible for their actions.
