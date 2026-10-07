-- Word of the Day: Rainmeter script (Lua 5.1).
-- Picks the current word from words.json and pushes it into the skin's meters.

-- ---- cycle logic (keep in sync with tools/wordctl.py and iphone/WordOfTheDay.js) ----

-- Days since 1970-01-01 for a calendar date (civil-from-days algorithm, no DST issues).
function DayNumber(y, m, d)
  if m <= 2 then y = y - 1 end
  local era = math.floor(y / 400)
  local yoe = y - era * 400
  local mp = (m + 9) % 12
  local doy = math.floor((153 * mp + 2) / 5) + d - 1
  local doe = yoe * 365 + math.floor(yoe / 4) - math.floor(yoe / 100) + doy
  return era * 146097 + doe - 719468
end

-- Weekly: 1970-01-01 was a Thursday; +4 puts week boundaries on Sundays.
function Period(n, mode)
  if mode == 'weekly' then return math.floor((n + 4) / 7) end
  return n
end

function CurrentIndex(data, y, m, d)
  local ay, am, ad = data.anchor.date:match('^(%d+)-(%d+)-(%d+)$')
  local elapsed = Period(DayNumber(y, m, d), data.mode)
    - Period(DayNumber(tonumber(ay), tonumber(am), tonumber(ad)), data.mode)
  return (data.anchor.index + elapsed) % #data.words -- Lua % is always non-negative here
end

function IsValid(data)
  if type(data) ~= 'table' or type(data.words) ~= 'table' or #data.words == 0 then return false end
  if data.mode ~= 'daily' and data.mode ~= 'weekly' then return false end
  if type(data.anchor) ~= 'table' or type(data.anchor.index) ~= 'number' then return false end
  if type(data.anchor.date) ~= 'string' or not data.anchor.date:match('^%d+-%d+-%d+$') then return false end
  for _, w in ipairs(data.words) do
    if type(w) ~= 'table' or type(w.word) ~= 'string' or type(w.definition) ~= 'string' then return false end
  end
  return true
end

-- ---- end cycle logic ----

-- Minimal JSON decoder (objects, arrays, strings, numbers, booleans, null).
function JsonDecode(s)
  local pos = 1

  local function ws()
    pos = s:find('[^ \t\r\n]', pos) or #s + 1
  end

  local function err(msg)
    error('json: ' .. msg .. ' at ' .. pos, 0)
  end

  local function utf8(cp)
    if cp < 0x80 then return string.char(cp) end
    if cp < 0x800 then
      return string.char(0xC0 + math.floor(cp / 0x40), 0x80 + cp % 0x40)
    end
    if cp < 0x10000 then
      return string.char(0xE0 + math.floor(cp / 0x1000), 0x80 + math.floor(cp / 0x40) % 0x40, 0x80 + cp % 0x40)
    end
    return string.char(0xF0 + math.floor(cp / 0x40000), 0x80 + math.floor(cp / 0x1000) % 0x40,
      0x80 + math.floor(cp / 0x40) % 0x40, 0x80 + cp % 0x40)
  end

  local escapes = { ['"'] = '"', ['\\'] = '\\', ['/'] = '/', b = '\b', f = '\f', n = '\n', r = '\r', t = '\t' }

  local value

  local function str()
    pos = pos + 1 -- opening quote
    local out = {}
    while true do
      local c = s:sub(pos, pos)
      if c == '' then err('unterminated string') end
      if c == '"' then pos = pos + 1; break end
      if c == '\\' then
        local e = s:sub(pos + 1, pos + 1)
        if e == 'u' then
          local cp = tonumber(s:sub(pos + 2, pos + 5), 16) or err('bad \\u escape')
          pos = pos + 6
          if cp >= 0xD800 and cp <= 0xDBFF and s:sub(pos, pos + 1) == '\\u' then
            local lo = tonumber(s:sub(pos + 2, pos + 5), 16) or err('bad \\u escape')
            cp = 0x10000 + (cp - 0xD800) * 0x400 + (lo - 0xDC00)
            pos = pos + 6
          end
          out[#out + 1] = utf8(cp)
        else
          out[#out + 1] = escapes[e] or err('bad escape')
          pos = pos + 2
        end
      else
        local stop = s:find('["\\]', pos) or #s + 1
        out[#out + 1] = s:sub(pos, stop - 1)
        pos = stop
      end
    end
    return table.concat(out)
  end

  local function obj()
    pos = pos + 1
    local t = {}
    ws()
    if s:sub(pos, pos) == '}' then pos = pos + 1; return t end
    while true do
      ws()
      if s:sub(pos, pos) ~= '"' then err('expected key') end
      local k = str()
      ws()
      if s:sub(pos, pos) ~= ':' then err('expected :') end
      pos = pos + 1
      t[k] = value()
      ws()
      local c = s:sub(pos, pos)
      pos = pos + 1
      if c == '}' then return t end
      if c ~= ',' then err('expected , or }') end
    end
  end

  local function arr()
    pos = pos + 1
    local t = {}
    ws()
    if s:sub(pos, pos) == ']' then pos = pos + 1; return t end
    while true do
      t[#t + 1] = value()
      ws()
      local c = s:sub(pos, pos)
      pos = pos + 1
      if c == ']' then return t end
      if c ~= ',' then err('expected , or ]') end
    end
  end

  value = function()
    ws()
    local c = s:sub(pos, pos)
    if c == '{' then return obj() end
    if c == '[' then return arr() end
    if c == '"' then return str() end
    for lit, v in pairs({ ['true'] = true, ['false'] = false }) do
      if s:sub(pos, pos + #lit - 1) == lit then pos = pos + #lit; return v end
    end
    if s:sub(pos, pos + 3) == 'null' then pos = pos + 4; return nil end
    local num = s:match('^-?%d+%.?%d*[eE]?[-+]?%d*', pos)
    if num and num ~= '' then pos = pos + #num; return tonumber(num) end
    err('unexpected character')
  end

  local result = value()
  ws()
  if pos <= #s then err('trailing data') end
  return result
end

-- ---- Rainmeter glue ----

local THEMES = {
  light = { bg = '255,255,255,235', text = '28,28,30,255', muted = '110,110,115,255' },
  dark = { bg = '28,28,30,235', text = '242,242,247,255', muted = '161,161,166,255' },
}

local data, lastBody, lastKey, cachePath, downloadPath, problem, startTime

local function readFile(path)
  local f = io.open(path, 'rb')
  if not f then return nil end
  local s = f:read('*a')
  f:close()
  return s
end

local function writeFile(path, s)
  local f = io.open(path, 'wb')
  if not f then return end
  f:write(s)
  f:close()
end

-- Returns the parsed data, or nil plus a reason.
local function tryParse(body)
  if not body or body == '' then return nil, 'empty' end
  body = body:gsub('^\239\187\191', '') -- strip a UTF-8 BOM if present
  local ok, parsed = pcall(JsonDecode, body)
  if not ok then return nil, tostring(parsed) end
  if not IsValid(parsed) then return nil, 'missing fields' end
  return parsed
end

local function setText(meter, text)
  SKIN:Bang('!SetOption', meter, 'Text', text)
end

local function render(theme)
  local t = THEMES[theme]
  SKIN:Bang('!SetVariable', 'BgColor', t.bg)
  SKIN:Bang('!SetOption', 'MeterLabel', 'FontColor', t.muted)
  SKIN:Bang('!SetOption', 'MeterWord', 'FontColor', t.text)
  SKIN:Bang('!SetOption', 'MeterPos', 'FontColor', t.muted)
  SKIN:Bang('!SetOption', 'MeterDefinition', 'FontColor', t.text)

  if data then
    local now = os.date('*t')
    local w = data.words[CurrentIndex(data, now.year, now.month, now.day) + 1]
    setText('MeterLabel', data.mode == 'weekly' and 'WORD OF THE WEEK' or 'WORD OF THE DAY')
    setText('MeterWord', w.word)
    setText('MeterPos', w.pos or '')
    setText('MeterDefinition', w.definition)
  else
    setText('MeterWord', problem and 'Not loaded' or 'Loading...')
    setText('MeterPos', '')
    setText('MeterDefinition', problem or 'Downloading the word list.')
  end

  SKIN:Bang('!UpdateMeter', '*')
  SKIN:Bang('!Redraw')
end

function Initialize()
  cachePath = SKIN:MakePathAbsolute('cache.json')
  downloadPath = SKIN:MakePathAbsolute('DownloadFile\\words.json')
  startTime = os.time()
  data = tryParse(readFile(cachePath))
end

-- Runs every second but only redraws when the data, the date, the theme or the status changes.
function Update()
  -- MeasureFetch saves words.json to disk; its string value is the saved file's path.
  local path = SKIN:GetMeasure('MeasureFetch'):GetStringValue()
  if not path:match('%.json$') then path = downloadPath end
  local body = readFile(path)
  if body and body ~= '' and body ~= lastBody then
    lastBody = body
    local parsed, err = tryParse(body)
    if parsed then
      data = parsed
      problem = nil
      writeFile(cachePath, body)
    else
      problem = 'Word list could not be read (' .. err .. ').'
      print('WordOfTheDay: ' .. problem)
    end
  end
  if not data and not problem and os.time() - startTime > 60 then
    problem = "Can't download the word list. Check the internet, then right-click > Refresh word list now."
  end

  local theme = SKIN:GetMeasure('MeasureTheme'):GetValue() == 1 and 'light' or 'dark'
  local key = os.date('%Y-%m-%d') .. theme .. tostring(data) .. tostring(problem)
  if key ~= lastKey then
    lastKey = key
    render(theme)
  end
  return ''
end
