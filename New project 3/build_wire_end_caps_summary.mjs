import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "C:\\Users\\bom\\Documents\\New project 3\\outputs\\wire_end_caps";
const outputPath = path.join(outputDir, "สรุปปลอกสี_Bandex_SC.xlsx");

const rows = [
  ["V-2", "น้ำตาล", "Bandex", "P0330550100216", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-2 (2.5) Brown น้ำตาล", "EA"],
  ["V-2", "ดำ", "Bandex", "P03305501G0216", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-2 (2.5) Black ดำ", "EA"],
  ["V-2", "เทา", "Bandex", "P03305501F0216", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-2 (2.5) Gray เทา", "EA"],
  ["V-2", "ฟ้า", "SC", "P0330550110182", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "INS-02 (2.5) Cyan ฟ้า", "EA"],
  ["V-2", "เขียว", "Bandex", "P03305501E0216", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-2 (2.5) Green เขียว", "EA"],
  ["V-3 / V-3.5", "น้ำตาล", "Bandex", "P0330550100316", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-3.5 (4) Brown น้ำตาล", "EA"],
  ["V-3 / V-3.5", "ดำ", "Bandex", "P03305501G0316", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-3.5 (4) Black ดำ", "EA"],
  ["V-3 / V-3.5", "เทา", "Bandex", "P03305501F0316", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-3.5 (4) Gray เทา", "EA"],
  ["V-3 / V-3.5", "ฟ้า", "SC", "P0330550110282", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "INS-03 (4) Cyan ฟ้า", "EA"],
  ["V-3 / V-3.5", "เขียว", "Bandex", "P03305501E0316", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-3.5 (4) Green เขียว", "EA"],
  ["V-5.5 / V-6", "น้ำตาล", "Bandex", "P0330550100416", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-5.5 (6) Brown น้ำตาล", "EA"],
  ["V-5.5 / V-6", "ดำ", "Bandex", "P03305501G0416", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-5.5 (6) Black ดำ", "EA"],
  ["V-5.5 / V-6", "เทา", "Bandex", "P03305501F0416", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-5.5 (6) Gray เทา", "EA"],
  ["V-5.5 / V-6", "ฟ้า", "SC", "P0330550110382", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "INS-04 (6) Cyan ฟ้า", "EA"],
  ["V-5.5 / V-6", "เขียว", "Bandex", "P03305501E0416", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-5.5 (6) Green เขียว", "EA"],
  ["V-8", "น้ำตาล", "Bandex", "P0330550100516", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-8 (10) Brown น้ำตาล", "EA"],
  ["V-8", "ดำ", "Bandex", "P03305501G0516", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-8 (10) Black ดำ", "EA"],
  ["V-8", "เทา", "Bandex", "P03305501F0516", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-8 (10) Gray เทา", "EA"],
  ["V-8", "ฟ้า", "SC", "P0330550110482", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "INS-05 (10) Cyan ฟ้า", "EA"],
  ["V-8", "เขียว", "Bandex", "P03305501E0516", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-8 (10) Green เขียว", "EA"],
  ["V-14", "น้ำตาล", "Bandex", "P0330550100616", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-14 (16) Brown น้ำตาล", "EA"],
  ["V-14", "ดำ", "Bandex", "P03305501G0616", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-14 (16) Black ดำ", "EA"],
  ["V-14", "เทา", "Bandex", "P03305501F0616", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-14 (16) Gray เทา", "EA"],
  ["V-14", "ฟ้า", "SC", "P0330550110582", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "INS-06 (16) Cyan ฟ้า", "EA"],
  ["V-14", "เขียว", "Bandex", "P03305501E0616", "Vinyl Wire End Caps ปลอกหุ้มหางปลา", "V-14 (16) Green เขียว", "EA"],
];

await fs.mkdir(outputDir, { recursive: true });

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("สรุปปลอกสี");
sheet.showGridLines = false;

sheet.getRange("A1:G1").merge();
sheet.getRange("A1").values = [["สรุปปลอกสี Vinyl Wire End Caps"]];
sheet.getRange("A2:G2").merge();
sheet.getRange("A2").values = [["Bandex เฉพาะสี น้ำตาล/ดำ/เทา/เขียว และใช้ SC สำหรับสีฟ้า ตามคำขอ"]];

const header = [["Size", "สี", "Brand", "Code", "ชื่อ", "Spec/Size", "Unit"]];
sheet.getRange("A4:G4").values = header;
sheet.getRangeByIndexes(4, 0, rows.length, 7).values = rows;

sheet.getRange("A1:G1").format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF", size: 14 },
  horizontalAlignment: "center",
};
sheet.getRange("A2:G2").format = {
  fill: "#EAF2F8",
  font: { color: "#1F2937" },
};
sheet.getRange("A4:G4").format = {
  fill: "#244062",
  font: { bold: true, color: "#FFFFFF" },
  borders: { preset: "all", style: "thin", color: "#1F2937" },
};
sheet.getRange(`A4:G${rows.length + 4}`).format = {
  borders: { preset: "all", style: "thin", color: "#D9E2EC" },
  wrapText: true,
};

sheet.getRange("A:A").format.columnWidthPx = 115;
sheet.getRange("B:B").format.columnWidthPx = 90;
sheet.getRange("C:C").format.columnWidthPx = 90;
sheet.getRange("D:D").format.columnWidthPx = 150;
sheet.getRange("E:E").format.columnWidthPx = 270;
sheet.getRange("F:F").format.columnWidthPx = 230;
sheet.getRange("G:G").format.columnWidthPx = 70;
sheet.freezePanes.freezeRows(4);
sheet.tables.add(`A4:G${rows.length + 4}`, true, "WireEndCapsSummary");

const preview = await workbook.render({
  sheetName: "สรุปปลอกสี",
  range: `A1:G${rows.length + 4}`,
  scale: 1,
  format: "png",
});
await fs.writeFile(path.join(outputDir, "preview.png"), new Uint8Array(await preview.arrayBuffer()));

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
});
await fs.writeFile(path.join(outputDir, "formula_errors.ndjson"), errors.ndjson, "utf8");

const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(outputPath);
console.log(outputPath);
