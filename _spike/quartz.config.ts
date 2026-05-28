import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

/**
 * Quartz 4 Configuration — su-kb-site SPIKE
 *
 * This is the disposable Stage 2 integration test for the clementine.syr.edu
 * styling fit. Once verified, contents promote to ../site/ per the plan.
 * See ../docs/decisions/0001-quartz-v4-as-ssg.md for the SSG choice.
 */
const config: QuartzConfig = {
  configuration: {
    pageTitle: "SU ITS Data & AI Knowledge Base",
    pageTitleSuffix: "",
    enableSPA: true,
    enablePopovers: true,
    analytics: null,
    locale: "en-US",
    baseUrl: "julianhernandez2155.github.io/su-kb-site",
    ignorePatterns: ["private", "templates", ".obsidian"],
    defaultDateType: "modified",
    theme: {
      fontOrigin: "local",
      cdnCaching: false,
      typography: {
        header: "Sherman Sans",
        body: "Sherman Sans",
        code: "ui-monospace",
      },
      colors: {
        lightMode: {
          light: "#ffffff",
          lightgray: "#eff0f1",
          gray: "#adb3b8",
          darkgray: "#404040",
          dark: "#000e54",
          secondary: "#000e54",
          tertiary: "#f76900",
          highlight: "rgba(247, 105, 0, 0.10)",
          textHighlight: "#fef0e6",
        },
        darkMode: {
          light: "#161618",
          lightgray: "#393639",
          gray: "#646464",
          darkgray: "#d4d4d4",
          dark: "#ebebec",
          secondary: "#ff8e00",
          tertiary: "#2b72d7",
          highlight: "rgba(247, 105, 0, 0.20)",
          textHighlight: "rgba(247, 105, 0, 0.30)",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({
        priority: ["frontmatter", "git", "filesystem"],
      }),
      Plugin.SyntaxHighlighting({
        theme: {
          light: "github-light",
          dark: "github-dark",
        },
        keepBackground: false,
      }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({
        enableSiteMap: true,
        enableRSS: true,
      }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.Favicon(),
      Plugin.NotFoundPage(),
    ],
  },
}

export default config
