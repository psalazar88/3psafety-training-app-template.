# 3P Safety – Sort your whole Gmail + Google Contacts (Windows)

The sorter turns your entire email history and contacts into one spreadsheet.
It tags every person as **Inspections / Training / Staffing**, records the dates you
last emailed them about each service, and removes newsletters and spam.
It also captures website form leads (Squarespace, Wix, WordPress, etc.) from the form
notification emails, including leads who left only a phone number.
Everything runs on your PC. Nothing is uploaded.

## 1. Download everything from Google (one time)
1. Go to **takeout.google.com**, signed in as patrick.salazar@3psafety.net.
2. Click **Deselect all**. Then check:
   - **Contacts** (format: CSV)
   - **Mail** (all mail)
3. Click **Next step**. Choose **Export once**, **.zip**, and **50 GB** as the file size. Then click **Create export**.
4. Google emails you a link when the export is ready, usually within a few hours.
   Download the zip file(s).
5. Right-click each zip and choose **Extract All...** into your **Downloads** folder.
   You should now have `Downloads\Takeout\Mail\...mbox` and `Downloads\Takeout\Contacts\...`.

> If Takeout says it's disabled, it's a Google Workspace setting. In the Admin console
> (admin.google.com), go to Apps → Additional Google services → Google Takeout → turn it ON.

## 2. Install Python (one time, 2 minutes)
1. Go to **python.org/downloads** and click **Download Python**.
2. Run the installer. **Check "Add python.exe to PATH"** at the bottom, then click Install Now.

## 3. Run the sorter
1. Put `sort_takeout.py` and `Run_3P_Sorter.bat` in the same folder, e.g. `Documents\3P`.
2. Double-click **Run_3P_Sorter.bat**.
   - If your Takeout folder isn't in Downloads, drag the folder into the window when asked.
3. It shows progress. Expect roughly 1–2 minutes per GB of mail.
4. When it's finished, the folder opens with two files:
   - **3P_master_contacts.csv**: one row per person (email, name, company, phone,
     last contact, within last 2 years, Inspections/Training/Staffing tags and dates)
   - **3P_companies.csv**: one row per customer company

## 4. Send it back
Upload **3P_master_contacts.csv** to Claude. It gets merged with your QuickBooks,
Zoho/Bigin, student, and website lists, then split into the Inspections, Training,
and Staffing lists for email checking (ZeroBounce) and Zoho.

## Keep it private
The Takeout download holds your entire email history and customer details. Keep it on
your PC or in a private folder. Don't put it in GitHub or a shared Drive folder.
Delete the Takeout folder when you're done.
