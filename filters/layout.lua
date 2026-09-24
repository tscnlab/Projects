-- Shared presentation only. All project prose stays in its canonical index.qmd.
local stringify = pandoc.utils.stringify
local function esc(value)
  return tostring(value):gsub('&', '&amp;'):gsub('<', '&lt;'):gsub('>', '&gt;'):gsub('"', '&quot;')
end
local function raw(value) return pandoc.RawBlock('html', value) end
function Pandoc(doc)
  if not FORMAT:match('html') then return doc end
  local file = assert(io.open(quarto.project.directory .. '/_generated/shared.json', 'r'))
  local shared = pandoc.json.decode(file:read('*a')); file:close()
  local lang = doc.meta.lang and stringify(doc.meta.lang) or 'en'
  local t = shared[lang]
  local function locations(values)
    local out = {}
    for _, v in ipairs(values) do
      local s = stringify(v)
      if lang == 'de' and s == 'Munich' then s = 'München' end
      if lang == 'de' and s == 'Remote' then s = 'Remote' end
      table.insert(out, s)
    end
    return table.concat(out, ' · ')
  end
  local function formats(values)
    local out = {}
    local names = { ["Master's thesis"]='Masterarbeit', ['Research internship']='Forschungspraktikum', ['Erasmus+ research placement']='Erasmus+ Forschungsaufenthalt', ['Engineering project']='Ingenieurprojekt' }
    for _, v in ipairs(values) do local s = stringify(v); table.insert(out, lang == 'de' and names[s] or s) end
    return table.concat(out, ' · ')
  end
  local nav = ''
  local paths = {'/', '/student-projects.html', '/jobs.html', '/about.html', '/expectations.html', '/funding.html', '/apply.html'}
  for i, name in ipairs(t.nav) do nav = nav .. '<a href="' .. paths[i] .. '">' .. esc(name) .. '</a>' end
  local header = '<a class="skip-link" href="#page-content">' .. (lang == 'de' and 'Zum Inhalt' or 'Skip to content') .. '</a><header class="site-header"><a class="brand" href="/" aria-label="' .. esc(shared.unit_name) .. ' - ' .. esc(t.nav[1]) .. '"><img src="/assets/tscn-logo.png" width="7660" height="1451" alt="' .. esc(shared.unit_name) .. '"></a><nav class="site-nav" aria-label="' .. (lang == 'de' and 'Hauptnavigation' or 'Main navigation') .. '">' .. nav .. '</nav></header>'
  local footer = '<footer class="site-footer"><div class="footer-description"><p>' .. esc(t.about_short) .. '</p><p class="last-updated">' .. esc(t.updated_label) .. ': <time datetime="' .. esc(shared.last_updated) .. '">' .. esc(t.updated_date) .. '</time></p></div><div class="footer-links"><a href="' .. shared.mission_url .. '">' .. (lang == 'de' and 'Leitbild' or 'Mission statement') .. '</a><a href="' .. shared.lab_url .. '">' .. (lang == 'de' and 'Website ↗' or 'Unit website ↗') .. '</a><a href="' .. shared.contact_url .. '">' .. (lang == 'de' and 'Kontakt' or 'Contact') .. '</a></div></footer>'
  local result = pandoc.List({raw(header)})
  local slug = doc.meta.slug and stringify(doc.meta.slug)
  if slug then
    local status = stringify(doc.meta.status)
    local status_label = status == 'open' and t.enquiry or (status == 'paused' and t.paused or t.closed)
    local top = '<main id="page-content"><div class="project-top"><a class="back-link" href="/student-projects.html">← ' .. esc(t.back) .. '</a><p class="eyebrow">' .. esc(t.label) .. '</p><h1>' .. esc(stringify(doc.meta.title)) .. '</h1><p class="project-subtitle">' .. esc(stringify(doc.meta.subtitle)) .. '</p><p class="project-meta">' .. esc(locations(doc.meta.location)) .. ' &nbsp; / &nbsp; ' .. (lang == 'de' and 'Deutsch' or 'English') .. '<br>' .. esc(formats(doc.meta.formats)) .. '</p><div class="project-actions"><a class="pdf-link" href="/projects/' .. slug .. '/advert.pdf" download>' .. esc(t.pdf) .. ' ↓</a><span class="availability">' .. esc(status_label) .. '</span></div></div><div class="project-layout"><div class="project-body">'
    result:insert(raw(top)); result:extend(doc.blocks)
    local bg = {}; for _, value in ipairs(doc.meta.backgrounds) do table.insert(bg, stringify(value)) end
    local aside = '</div><aside class="project-aside"><section><h2>' .. esc(t.backgrounds) .. '</h2><p>' .. esc(table.concat(bg, ' · ')) .. '</p><p class="small">' .. esc(t.fit_note) .. '</p></section><section><h2>' .. esc(t.expectations_title) .. '</h2><p>' .. esc(t.expectations_short) .. '</p>'
    if lang == 'en' then aside = aside .. '<a href="/expectations.html">General expectations →</a>' end
    aside = aside .. '</section><section><h2>' .. esc(t.funding_title) .. '</h2><p>' .. esc(t.funding_short) .. '</p>'
    if lang == 'en' then aside = aside .. '<a href="/funding.html">Funding information →</a>' end
    aside = aside .. '</section></aside></div><section class="apply-strip"><h2>' .. esc(t.apply_title) .. '</h2><p>' .. esc(t.application_short) .. '</p><div class="contact-links"><a href="mailto:' .. shared.contacts.Munich .. '">' .. (lang == 'de' and 'München' or 'Munich') .. ': ' .. shared.contacts.Munich .. '</a><a href="mailto:' .. shared.contacts['Tübingen'] .. '">Tübingen: ' .. shared.contacts['Tübingen'] .. '</a></div></section><p class="project-note">' .. esc(t.location_note) .. '</p></main>'
    result:insert(raw(aside))
  else
    local is_wide = quarto.doc.input_file:match('index.qmd$') or quarto.doc.input_file:match('student%-projects.qmd$')
    result:insert(raw('<main id="page-content"' .. (is_wide and '' or ' class="text-page"') .. '>'))
    result:extend(doc.blocks); result:insert(raw('</main>'))
  end
  result:insert(raw(footer)); doc.blocks = result; return doc
end
