# Prompt — Add "Smart QR Print" to the MAAN COPIERS app

Copy everything below the line and paste it to your AI coding assistant inside the Maan Copiers repo.

---

## Context

This repo is the MAAN COPIERS web app (single-file `index.html`, Supabase backend at the project already configured in `SUPABASE_URL` / `SUPABASE_ANON_KEY`, staff log in with email + password via `supabase.auth.signInWithPassword`, staff access is checked through the `memberships` table using `org_id` — live org `d7334fe5-1e03-4092-8f43-555113fcda96`, demo org `d7334fe5-1e03-4092-8f43-555113fcda97`). The app already has job tickets, thermal-printer slips, WhatsApp "order ready" messages, parties, payments and reports. Keep the existing look, coding style and Live/Demo mode behaviour.

## Goal

Add a **Smart QR Print** feature so walk-in customers stop sending files on WhatsApp. One QR code stuck on the counter lets a customer:

**scan QR → upload file → choose print settings → pay → get an order number → collect from the counter.**

No app install, no WhatsApp, no login for the customer. The owner's PC receives the order instantly and it goes straight to the printer.

The customer page must be bright, clean and mobile-first: white cards, MAAN COPIERS red as the accent, rounded corners, big tap targets.

## Part 1 — Customer page (`print.html`, public, no login)

Make it a separate lightweight page so it loads fast on mobile data. It opens from the QR code.

1. **Welcome / Upload**
   - Header: MAAN COPIERS wordmark plus the tagline "Print it. Skip the queue."
   - A large "Tap to select file" upload area. Accept PDF, JPG/PNG/HEIC photos, DOC/DOCX and PPT/PPTX, up to 50 MB.
   - A three-step "How it works" strip: Upload → Settings → Collect.
   - Show an upload progress bar with the file name, like "Uploading Assignment.pdf… 62%".
   - Count the pages automatically:
     - PDF: use pdf.js.
     - Images: 1 page each.
     - Word/PPT: ask the customer to type the page count.
   - Allow multiple files in one order. Each file gets its own settings.

2. **Print settings** (a step indicator at the top shows Upload ✓ — Settings — Pay)
   - A file row with the name, page count and a "Change" button.
   - **Live preview** of the printed sheet using pdf.js thumbnails. It updates instantly when settings change: greyscale for B&W, the N-up grid for pages-per-sheet, and sheet "1 / 7" with Previous / Next.
   - **Colour:** segmented control, Black & white | Full colour.
   - **Paper size:** A4 | A3 | Letter | Legal.
   - **Double-sided:** toggle switch.
   - **Copies:** − / + stepper.
   - **Pages per sheet:** tiles for 1×1, 1×2, 2×2 and 3×3 (that is 1, 2, 4 and 9 pages on one side).
   - **More options** (collapsed): page range ("All" or custom like `1-3,5,8`), name, mobile number (for the WhatsApp "ready" message) and a note for the shop.
   - **Sticky bottom bar:** live total ₹, a summary like "7 sheets · B&W · A4 · Double", and a red button "Pay & send to counter".
   - **Price calculation:**
     - sides = ceil(selected pages ÷ pages-per-sheet)
     - sheets = double-sided ? ceil(sides ÷ 2) : sides
     - amount = sides × rate(colour, paper, single/double) × copies
   - Read the rates from the existing `services` table, so the owner changes prices in one place. If that is not possible, add a small "QR Print rates" settings screen in the staff app.

3. **Payment**
   - A bottom sheet: **Pay now with UPI** (`upi://pay?pa=<shop UPI>&pn=MAAN COPIERS&am=<amount>&cu=INR&tn=MAAN QR #<order>`) or **Pay at counter**.
   - Store `payment_method` as `upi` or `counter`, and `payment_status` as `unpaid` or `claimed`. Staff confirm UPI payments from the counter screen.
   - Keep the design ready to plug in Razorpay or PhonePe auto-verification later.

4. **Sending + order number**
   - A "Sending to counter…" overlay with a progress bar.
   - Then a success screen:
     - big order number **#032** (resets daily);
     - live status tracker **Received → Printing → Ready → Collected** (updates via Supabase Realtime or polling);
     - amount, payment status, and "Show this number at the counter".
   - Save the order in localStorage so reopening the page shows its status.
   - A "Print another file" button.

## Part 2 — Counter / Owner screen (inside the staff app, new "QR Orders" tab)

- Show a live **kanban** with columns New → Printing → Ready → Delivered, for today plus yesterday's pending orders.
- Play a "ding" and show a toast when a new order arrives (Supabase Realtime on the orders table).
- **Order card:**
  - big `#032`, time ago, file name(s) and page count;
  - chips: B&W/Colour, A4, Double-sided, 2×2, ×2 copies;
  - sheets used, ₹ amount and payment badge (UPI claimed / Paid / Pay at counter);
  - customer name and phone.
- **Actions:**
  - Print, Reprint, Mark paid, Ready, Delivered;
  - Ready sends the existing WhatsApp "Your order #032 is ready at MAAN COPIERS" message;
  - Download original.
- **Auto-print toggle (the "no print button" feature):**
  - When ON, every new order is printed automatically and moved to Printing.
  - Build a **print-ready PDF in the browser with pdf-lib**:
    - apply the page range and N-up layout (rotate pages for 2-up when that fits better);
    - use the paper size;
    - repeat for copies, adding a blank page between copies when double-sided and the side count is odd;
    - convert images onto pages.
  - Send it to a hidden iframe and call `print()`.
  - Explain in the UI that silent printing needs Chrome started with `--kiosk-printing` on the counter PC. Mention that a tiny local print agent can be added later for per-order colour/duplex printer control.
  - Show a big B&W/COLOUR badge so the operator picks the right tray when needed.
- **When marked Delivered:**
  - optionally create a normal job ticket / sale entry so QR orders appear in existing reports, party ledgers and sheet/material consumption (paper used = sheets × copies, on the selected machine);
  - delete the uploaded file from storage for customer privacy.
- **"Shop QR poster" button:** generates a printable A4 poster with:
  - MAAN COPIERS and the large QR (pointing to `print.html`);
  - "Scan karo · Upload karo · Counter se lo";
  - "No WhatsApp · No line · No galti".
- Add a small **QR Print report**: orders per day, pages, sheets, amount, UPI vs cash.

## Part 3 — Supabase

Provide one SQL migration file:

1. **Table `qr_print_orders`**
   - Columns: `id uuid pk`, `org_id`, `order_no int` (daily sequence, set by a trigger with an advisory lock, reset each day in Asia/Kolkata time), `order_date`, `created_at`, `updated_at`, `customer_name`, `customer_phone`, `status` (`new|printing|ready|delivered|cancelled`), `payment_method`, `payment_status` (`unpaid|claimed|paid`), `amount`, `notes`, `job_ticket_id` (nullable link).
   - Child table `qr_print_order_files`: `order_id`, `file_path`, `file_name`, `mime`, `size`, `pages`, `page_range`, `print_pages`, `color`, `paper`, `duplex`, `copies`, `pps`, `sides`, `sheets`, `amount`.
2. **Private storage bucket `qr-print-files`** with a 50 MB limit.
3. **RLS:**
   - Customers (`anon`) can only upload into the bucket and call SECURITY DEFINER RPCs:
     - `qr_print_submit(payload jsonb)` → returns `{id, order_no}`. It validates every field and **recalculates the amount on the server** from the rates.
     - `qr_print_order_status(p_id uuid)` → returns only order_no, status and payment_status.
   - Customers can never list or read other orders or files.
   - Staff (a member of the org in `memberships`) can select/update orders and read/delete files.
4. Add `qr_print_orders` to the `supabase_realtime` publication.
5. Add a scheduled cleanup (pg_cron or an edge function) that deletes files older than 3 days.

## Acceptance checks

- On a phone over mobile data, a 20-page PDF upload with 2×2 double-sided B&W shows the correct preview and price: 5 sides → 3 sheets.
- The order appears on the counter screen within 2 seconds with a sound, and auto-prints correctly laid out.
- Ready → the customer's page updates to "Ready" and the WhatsApp message opens.
- An anonymous user cannot read any other order (test with the anon key).
- Works in the existing Demo org without touching live data.
- Mobile layout works at 360 px width; the counter screen works on a desktop.
