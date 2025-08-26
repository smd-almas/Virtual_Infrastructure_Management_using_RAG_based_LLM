# Append a CSV row:
# usage: log_row metric case value unit output_file
log_row() {
  ts=$(date -Iseconds)
  metric="$1"
  case_name="$2"
  value="$3"
  unit="$4"
  outfile="$5"
  printf '%s,%s,%s,%s,%s\n' "$ts" "$metric" "$case_name" "$value" "$unit" >> "$outfile"
}
