# Add Copy Summary to Simple View
# Adds a button to copy calculation summary to clipboard

file_path = r"c:\Users\shuli\Downloads\Calculator\index.html"

LINE_END = b'\r\n'

with open(file_path, 'rb') as f:
    content = f.read()

# Find the spot after the Landed Unit display (line 696 area)
# Look for the closing of the Landed Unit section and add button there

# Target: After "</div>" that closes the landed section (around line 697)
# Insert after: <span className={hasPack ? "text-lg font-bold..." pattern

target = b'<span className={hasPack ? "text-lg font-bold text-gray-900 dark:text-white" : "text-xl font-bold text-gray-900 dark:text-white"}>{money(landedUnit)}</span>'
target_end = b'</div>'

# Find position
pos = content.find(target)
if pos == -1:
    print("Could not find landed unit target")
    exit(1)

# Find the double </div> after this
after_target = content[pos:pos+500]
first_close = after_target.find(b'</div>')
second_close = after_target.find(b'</div>', first_close + 6)

insert_pos = pos + second_close + len(b'</div>')

# Create Copy Summary button and function
copy_summary = '''
                                {/* Copy Summary Button */}
                                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                                    <button 
                                        onClick={() => {
                                            const summary = [
                                                `Target Sell: ${money(finalSell)}`,
                                                `Margin: ${marginPct.toFixed(1)}%`,
                                                `Profit: ${money(profit)}`,
                                                `Landed (Unit): ${money(landedUnit)}`,
                                                hasPack ? `Landed (Pack): ${money(landedPack)}` : '',
                                                `Units/40HQ: ${units.toLocaleString()}`,
                                                `Cartons: ${cartonsCount.toLocaleString()}`
                                            ].filter(Boolean).join('\\n');
                                            navigator.clipboard.writeText(summary);
                                            const btn = event.target;
                                            const orig = btn.textContent;
                                            btn.textContent = '\\u2713 Copied!';
                                            btn.classList.add('!bg-green-500', '!text-white');
                                            setTimeout(() => { btn.textContent = orig; btn.classList.remove('!bg-green-500', '!text-white'); }, 2000);
                                        }}
                                        className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-sm font-bold text-gray-700 dark:text-gray-300 transition-all"
                                    >
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                                        Copy Summary
                                    </button>
                                </div>'''

copy_bytes = copy_summary.encode('utf-8').replace(b'\n', LINE_END)

new_content = content[:insert_pos] + LINE_END + copy_bytes + content[insert_pos:]

with open(file_path, 'wb') as f:
    f.write(new_content)

print("Added Copy Summary button to Simple view!")
print(f"Inserted at position {insert_pos}")
