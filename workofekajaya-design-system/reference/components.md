# Components — Work of Ekajaya

Copy-paste vocabulary. Every snippet is taken from, or consistent with, the live site.

## Section shell

```astro
<section id="projects" class="relative z-20 bg-background border-t border-border">
  <div class="max-w-3xl mx-auto px-6 py-24 md:py-32">
    <header class="mb-16">
      <p class="font-mono text-xs tracking-[0.3em] text-accent mb-3">PROJECTS</p>
      <h2 class="font-[family-name:var(--font-display)] text-3xl md:text-5xl font-bold text-foreground text-balance">
        Selected projects.
      </h2>
    </header>
    <!-- content -->
  </div>
</section>
```

Valid section ids (must match `BaseLayout.astro` nav dots): `hero`, `about`, `experience`,
`projects`, `skills`, `contact`.

## Eyebrow

```astro
<p class="font-mono text-xs tracking-[0.3em] text-accent mb-3">EXPERIENCE</p>
```

Uppercase. `tracking-[0.3em]` is fixed — do not reduce it. Red is the only color used here.

## Tech chip (interactive)

```astro
<span class="inline-block px-3 py-1 text-xs font-mono border border-border rounded-full text-muted-foreground hover:border-accent hover:text-accent transition-colors">
  Spring Boot
</span>
```

## Micro chip (static)

```astro
<span class="text-[10px] font-mono px-2 py-1 border border-border rounded-full text-muted-foreground">
  PostgreSQL
</span>
```

Use for tags, stack lists, and metadata. No hover state.

## Card

```astro
<article class="group p-6 md:p-8 border border-border rounded-xl hover:border-accent transition-colors">
  <div class="flex flex-col md:flex-row md:items-baseline md:justify-between gap-1 mb-3">
    <h3 class="text-lg font-bold text-foreground group-hover:text-accent transition-colors">
      Project name
    </h3>
    <time class="font-mono text-xs text-muted-foreground">Jan — May 2024</time>
  </div>

  <p class="text-sm text-muted-foreground leading-relaxed mb-4 text-pretty">Description.</p>

  <div class="flex flex-wrap gap-2">
    <span class="px-2 py-1 text-[10px] font-mono border border-border rounded-full text-muted-foreground">Astro</span>
  </div>
</article>
```

The `group` + `group-hover:text-accent` pairing is the standard hover affordance.

## External link with icon

```astro
---
import { Icon } from 'astro-icon/components';
---

<a
  href={href}
  target="_blank"
  rel="noopener noreferrer"
  class="inline-flex items-center gap-1.5 hover:underline underline-offset-4 decoration-accent/50"
>
  {name}
  <Icon name="lucide:external-link" size={14} class="opacity-50" />
</a>
```

## Buttons

```astro
<!-- Primary -->
<a href="mailto:contact@workofekajaya.com"
   class="inline-flex items-center gap-2 px-6 py-3 bg-foreground text-background rounded-md font-mono text-sm font-medium active:scale-[0.96] transition-transform w-fit">
  <Icon name="lucide:mail" size={16} />
  Email me
</a>

<!-- Secondary -->
<a href="https://github.com/ekajaya740" target="_blank" rel="noopener noreferrer"
   class="inline-flex items-center gap-2 px-6 py-3 border border-border rounded-md font-mono text-sm font-medium hover:bg-secondary hover:border-foreground active:scale-[0.96] transition-colors w-fit">
  <Icon name="lucide:github" size={16} />
  GitHub
</a>
```

Only **one** primary button per group. The rest are secondary.

## Entry list (experience / timeline)

```astro
<article class="group">
  <div class="flex flex-col md:flex-row md:items-baseline md:justify-between gap-1 mb-3">
    <h3 class="text-lg font-bold text-foreground">{exp.role}</h3>
    <time class="font-mono text-xs text-muted-foreground">{exp.period}</time>
  </div>

  <p class="font-mono text-sm text-accent mb-3">{exp.org}</p>

  <ul class="space-y-2">
    {exp.highlights.map((h) => (
      <li class="text-sm text-muted-foreground leading-relaxed flex items-start gap-2">
        <span class="mt-1.5 w-1 h-1 rounded-full bg-muted-foreground flex-shrink-0" />
        <span>{h}</span>
      </li>
    ))}
  </ul>
</article>
```

## Two-column chip grid

```astro
<div class="grid grid-cols-1 sm:grid-cols-2 gap-8">
  {groups.map((group) => (
    <div>
      <h3 class="text-sm font-bold text-foreground mb-3 font-mono tracking-wide">{group.category}</h3>
      <ul class="flex flex-wrap gap-2">
        {group.items.map((item) => (
          <li class="text-xs font-mono px-2 py-1 bg-secondary border border-border rounded-full text-muted-foreground">
            {item}
          </li>
        ))}
      </ul>
    </div>
  ))}
</div>
```

## Sub-block with divider

For secondary content inside a section (e.g. education under skills):

```astro
<div class="mt-20 pt-12 border-t border-border">
  <header class="mb-8">
    <p class="font-mono text-xs tracking-[0.3em] text-accent mb-3">EDUCATION & CERTIFICATIONS</p>
  </header>
  <!-- content -->
</div>
```

## Nav dots (in `BaseLayout.astro`)

```astro
<a href="#hero" class="section-dot group relative flex items-center p-3"
   data-section="hero" aria-label="Hero">
  <span class="section-dot-label tracking-wider font-mono text-[10px] md:text-xs opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0 transition-[opacity,transform] duration-300 text-muted-foreground absolute right-full mr-2 md:mr-3 whitespace-nowrap">HERO</span>
  <span class="w-2 h-2 md:w-2.5 md:h-2.5 rounded-full bg-muted-foreground/50 hover:bg-foreground transition-colors duration-300" />
</a>
```

Active state is applied by script: the dot span swaps `bg-muted-foreground/50` → `bg-accent`
with `scale(1.5)`, and the label swaps `text-muted-foreground` → `text-accent`. The script
targets `.section-dot > span:last-child` and `.section-dot-label`, so **keep that structure** —
adding spans inside a dot will break the active-state indexing.

## Blog list item

```astro
<article class="group border-b border-border pb-8 hover:border-accent transition-colors">
  <a href={`/blog/${post.id}/`} class="block">
    <div class="flex flex-col md:flex-row md:items-baseline md:justify-between gap-2 mb-2">
      <h2 class="text-lg font-bold text-foreground group-hover:text-accent transition-colors">
        {post.data.title}
      </h2>
      <time class="font-mono text-xs text-muted-foreground">{formatted}</time>
    </div>
    <p class="text-sm text-muted-foreground leading-relaxed mb-3">{post.data.description}</p>
    <div class="flex flex-wrap gap-2">
      {post.data.tags.map((tag) => (
        <span class="text-[10px] font-mono px-2 py-1 border border-border rounded-full text-muted-foreground">{tag}</span>
      ))}
    </div>
  </a>
</article>
```

## Icons

```astro
import { Icon } from 'astro-icon/components';

<Icon name="lucide:external-link" size={14} class="opacity-50" />
```

Currently allowlisted in `astro.config.mjs`: `mail`, `github`, `link`, `linkedin`,
`external-link`. **Adding an icon requires adding it to that allowlist**, or it renders nothing.

## Class merging

```ts
import { cn } from '@/lib/utils';

cn('relative mx-auto h-full w-full', className);
```

`cn` is re-exported from the `cn` package (shadcn's drop-in replacement for
`clsx` + `tailwind-merge`). Do not reintroduce those two dependencies.
