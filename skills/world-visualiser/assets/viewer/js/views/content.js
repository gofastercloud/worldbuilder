// content.js: Interactive reader for generated short stories, D&D 5e campaigns, and chapters.
(function () {
  'use strict';
  if (typeof WB === 'undefined' || !WB || !WB.registerView) return;
  const { el } = WB.util;
  const D = WB.data;

  const KIND_LABELS = {
    story: 'Story',
    campaign: '5e Campaign',
    chapter: 'Chapter',
  };

  WB.registerView({
    id: 'content', title: 'Content', order: 70,
    create(container) {
      container.classList.add('cnt');
      const items = Array.isArray(D.content) ? D.content : [];
      const opts = {
        kind: 'all',
        selectedId: items.length ? items[0].id : null,
      };

      const filterKinds = [
        { key: 'all', label: 'All' },
        { key: 'story', label: 'Stories' },
        { key: 'campaign', label: '5e Campaigns' },
        { key: 'chapter', label: 'Chapters' },
      ];
      const filterBtns = new Map();
      const seg = el('div', { class: 'cnt-seg', role: 'group', 'aria-label': 'Filter content by kind' });
      filterKinds.forEach((fk) => {
        const b = el('button', {
          type: 'button',
          class: 'cnt-seg-btn',
          'aria-pressed': String(opts.kind === fk.key),
          text: fk.label,
        });
        b.addEventListener('click', () => {
          opts.kind = fk.key;
          filterBtns.forEach((btn, k) => btn.setAttribute('aria-pressed', String(k === fk.key)));
          render();
        });
        filterBtns.set(fk.key, b);
        seg.appendChild(b);
      });

      const countEl = el('span', { class: 'muted', role: 'status' });
      const copyBtn = el('button', {
        type: 'button',
        class: 'btn cnt-copy-btn',
        text: 'Copy Markdown',
        hidden: !items.length,
      });
      copyBtn.addEventListener('click', () => {
        const cur = items.find((x) => x.id === opts.selectedId);
        if (!cur || !navigator.clipboard) return;
        navigator.clipboard.writeText(cur.markdown || '').then(() => {
          copyBtn.textContent = 'Copied ✓';
          setTimeout(() => { copyBtn.textContent = 'Copy Markdown'; }, 1600);
        }).catch(() => {});
      });

      const bar = el('div', { class: 'cnt-bar' }, seg, countEl, el('span', { class: 'cnt-spacer' }), copyBtn);
      const layout = el('div', { class: 'cnt-layout' });
      const sidebar = el('aside', { class: 'cnt-sidebar', 'aria-label': 'Content library' });
      const reader = el('article', { class: 'cnt-reader', 'aria-label': 'Content reader' });
      layout.append(sidebar, reader);
      container.append(bar, layout);

      // Delegate clicks on inline entity links inside rendered Markdown
      reader.addEventListener('click', (ev) => {
        const btn = ev.target && ev.target.closest ? ev.target.closest('.cnt-entity-link') : null;
        if (!btn) return;
        const slug = btn.getAttribute('data-entity');
        if (slug && WB.nodeById && WB.nodeById.has(slug)) {
          WB.select(slug);
        }
      });

      function matches(item) {
        if (opts.kind !== 'all' && item.kind !== opts.kind) return false;
        const q = (WB.state.filters.search || '').trim().toLowerCase();
        if (q) {
          const hay = (item.title + ' ' + (item.summary || '') + ' ' + (item.era || '') + ' ' + (item.anchor || '')).toLowerCase();
          if (!hay.includes(q)) return false;
        }
        return true;
      }

      function renderReader(item) {
        if (!item) {
          reader.replaceChildren(
            el('div', { class: 'cnt-empty' },
              el('h3', { text: 'No matching content' }),
              el('p', { text: 'Try clearing your search or switching the filter above.' })));
          copyBtn.hidden = true;
          return;
        }
        copyBtn.hidden = false;
        const pills = [
          el('span', { class: 'cnt-pill cnt-pill-' + item.kind, text: KIND_LABELS[item.kind] || item.kind }),
        ];
        if (item.is_brief) pills.push(el('span', { class: 'cnt-pill cnt-pill-brief', text: 'Brief' }));
        if (item.date) pills.push(el('span', { class: 'cnt-pill', text: item.date }));
        else if (item.era) pills.push(el('span', { class: 'cnt-pill', text: item.era }));
        if (item.system) pills.push(el('span', { class: 'cnt-pill', text: item.system }));
        if (item.level) pills.push(el('span', { class: 'cnt-pill', text: 'Levels ' + item.level }));
        if (item.subgenre) pills.push(el('span', { class: 'cnt-pill', text: item.subgenre }));
        pills.push(el('span', {
          class: 'cnt-pill cnt-pill-muted',
          text: item.word_count.toLocaleString() + ' words · ' + item.read_minutes + ' min read',
        }));

        const head = el('header', { class: 'cnt-doc-head' },
          el('div', { class: 'cnt-pills' }, pills),
          el('div', { class: 'cnt-path', text: item.rel_path }));

        const prose = el('div', { class: 'cnt-prose' });
        prose.innerHTML = item.html || '';

        reader.replaceChildren(head, prose);
        reader.scrollTop = 0;
      }

      function render() {
        filterKinds.forEach((fk) => {
          const cnt = fk.key === 'all' ? items.length : items.filter((x) => x.kind === fk.key).length;
          const btn = filterBtns.get(fk.key);
          if (btn) btn.textContent = fk.label + ' (' + cnt + ')';
        });

        if (!items.length) {
          countEl.textContent = '0 items';
          copyBtn.hidden = true;
          sidebar.hidden = true;
          reader.replaceChildren(
            el('div', { class: 'cnt-empty' },
              el('h3', { text: 'No stories or campaigns yet' }),
              el('p', {}, 'Generate dated short stories or D&D 5e campaigns with ',
                el('code', { text: 'story_campaign.py' }), ' (or ',
                el('code', { text: '/wb-story' }), ' and ',
                el('code', { text: '/wb-campaign' }), ') and save them in ',
                el('code', { text: 'stories/' }), ', ',
                el('code', { text: 'output/stories/' }), ', or ',
                el('code', { text: 'output/campaigns/' }), '.'),
              el('p', {}, 'Refresh or rebuild the viewer afterwards to read them here with clickable entity links.')));
          return;
        }

        sidebar.hidden = false;
        const shown = items.filter(matches);
        countEl.textContent = shown.length + ' of ' + items.length + (items.length === 1 ? ' item' : ' items');

        if (shown.length && !shown.some((x) => x.id === opts.selectedId)) {
          opts.selectedId = shown[0].id;
        }

        sidebar.replaceChildren(
          ...shown.map((item) => {
            const active = item.id === opts.selectedId;
            return el('button', {
              type: 'button',
              class: 'cnt-item' + (active ? ' active' : ''),
              'aria-pressed': String(active),
              onclick: () => {
                opts.selectedId = item.id;
                render();
              },
            },
            el('div', { class: 'cnt-item-top' },
              el('span', { class: 'cnt-pill cnt-pill-' + item.kind, text: KIND_LABELS[item.kind] || item.kind }),
              item.is_brief ? el('span', { class: 'cnt-pill cnt-pill-brief', text: 'Brief' }) : null,
              el('span', { class: 'cnt-item-words', text: item.word_count.toLocaleString() + 'w' })),
            el('div', { class: 'cnt-item-title', text: item.title }),
            item.summary ? el('div', { class: 'cnt-item-sum', text: item.summary }) : null);
          })
        );

        const activeItem = shown.find((x) => x.id === opts.selectedId) || null;
        renderReader(activeItem);
      }

      this.onFilter = () => render();
      this.activate = () => render();
      render();
    },
  });
})();
