# tastejs/todomvc 吞噬记录 — devour_tentacle
> 吞噬日期: 2026-09-11T12:13:12 | 来源: https://github.com/tastejs/todomvc
> Stars: 28957 | 语言: JavaScript | 许可: NOASSERTION

## 项目概览
- 描述: Helping you select a JavaScript framework - Todo apps for React.js, Angular, Vue and many more
- 主题: (无)
- 分支: master | 最近推送: 2026-06-06

## README 摘要
# ![TodoMVC](media/logo.png)

> Helping you select a JavaScript framework

### [Website](http://todomvc.com)&nbsp;&nbsp;&nbsp;&nbsp;[Blog](http://blog.tastejs.com)&nbsp;&nbsp;&nbsp;&nbsp;[TasteJS](http://tastejs.com)

Developers have a number of choices today when it comes to selecting a JavaScript framework or UI library for building scalable web apps.

React, Vue, Svelte, Angular, Solid, Lit... the list of solutions continues to grow, but just how do you decide on which to use in a sea of so many options?

To help solve this problem, we created TodoMVC - a project which offers the same Todo application implemented in most of the popular JavaScript frameworks of the day. Each example is functionally identical and follows the same [app specification](app-spec.md), so you can compare syntax, structure, and idioms side by side on equal footing.

TodoMVC has been the de-facto teaching example for UI frameworks for over a decade, and forms the core of the cross-browser [Speedometer](https://browserbench.org/Speedometer3.1/) benchmark used by every major browser engine to optimize UI performance.


## Examples

The actively maintained examples in this repo are kept current with their framework's latest stable line. As of TodoMVC 2.0:

- [React 19](examples/react)
- [Vue 3.5](examples/vue)
- [Angular 21](examples/angular)
- [Svelte 5](examples/svelte) (with runes)
- [Preact 10](examples/preact)
- [Lit 3.3](examples/lit)
- [React Redux 9](examples/react-redux) (with Redux Toolkit 2)

Plenty of legacy framework showcases also live in `examples/` for historical reference. See the [website](http://todomvc.com) for the full list.


## Build a TodoMVC App with Your AI Coding Agent

The [app spec](app-spec.md) is plain Markdown and reads cleanly into any modern AI coding agent (Claude Code, Cursor, GitHub Copilot, Codex, Gemini Code Assist, Aider, and so on). To generate a fresh implementation in a framework or language that isn't on the list above, drop this prompt into your agent of choice:

```
Build a TodoMVC app following this spec https://raw.githubusercontent.com/tastejs/todomvc/refs/heads/master/app-spec.md in React
```

Replace `React` with `Vue`, `Svelte`, `Angular`, `Solid`, `Lit`, `Preact`, `Qwik`, or any framework or language you want to evaluate. The result follows the same behavioural surface every example in this repo implements (add, edit, toggle, filter, route, clear completed), so it's directly comparable to the reference apps.


## Running the examples and tests

Each example builds and serves itself. Most modern apps use Vite, webpack, or rollup; cd into an example, install, and run:

```sh
$ cd examples/react
$ npm install
$ npm run build
$ npm run serve
```

To run the Cypress test suite against the maintained examples:

```sh
$ npm install
$ npm run test:all
```

`npm run test:all` defaults to the curated modern set. Pass `--all` to sweep every example in `examples/`, or `--framework=react` to target a single one. See [tests/README.md](tests/README.md) for details.


## Team

TodoMVC would not be possible without a strong team of [contributors](https://github.com/tastejs/todomvc/contributors) helping push the project forward each day. Additionally, we have a core project team composed of:

#### [Addy Osmani](https://github.com/addyosmani) - Founder/Lead

<img align="left" width="40" height="40" src="https://avatars.githubusercontent.com/u/110953?v=4&s=40">
  Addy is a Software Engineer at Google who originally created TodoMVC. He oversees the project direction, maintenance and organizes the planning and development efforts of the team.

#### [Sindre Sorhus](https://github.com/sindresorhus) - Lead Developer

<img align="left" width="40" height="40" src="https://avatars.githubusercontent.com/u/170270?v=4&s=40">
Sindre is a Web Developer who leads core development, quality control and application design for the project. His engineering contributions have helped us ensure consistency and best practices are enforced wherever possible. Sindre also leads up development of the TodoMVC application spec.

#### [Pascal Hartig](https://github.com/passy) - Developer

<img align="left" width="40" height="40" src="https://avatars.githubusercontent.com/u/9906?v=4&s=40">
Pascal is a Software Engineer at Twitter with a deep passion for consistency. He watches pull requests and helps developers getting their contributions integrated with TodoMVC.

#### [Stephen Sawchuk](https://github.com/stephenplusplus) - Developer

<img align="left" width="40" height="40" src="https://avatars3.githubusercontent.com/u/723048?v=2&s=40">
Stephen is a Front-end Engineer at Quicken Loans that cares about improving the maintainability and developer experience of open-source projects. His recent contributions include helping us move all apps over to using Bower and implementing the new information bar.

#### [Colin Eberhardt](https://github.com/colineberhardt) - Developer

<img align="left" width="40" height="40" src="https://avatars.githubusercontent.com/u/1098110?v=4&s=40">
Colin is a software consultant at Scott Logic who is passionate about all software - from JavaScript to Java, and C# to Objective-C. His recent contribution to the project has been a fully automated test suite.

#### [Sam Saccone](https://github.com/samccone) - Developer

<img align="left" width="40" height="40" src="https://avatars.githubusercontent.com/u/883126?v=4&s=40">
Sam is a Software Engineer at Google who is driven by an endless desire to create, solve problems, and improve developers' lives.

#### [Arthur Verschaeve](https://github.com/arthurvr) - Developer

<img align="left" width="40" height="40" src="https://avatars.githubusercontent.com/u/6025224?v=4&s=40">
Arthur is an open-source fanboy from Belgium. He is passionate about developer tooling and all things JavaScript.

#### [Fady Samir Sadek](https://github.com/FadySamirSadek) - Developer

<img align="left" width="40" height="40" src="https://avatars.githubusercontent.com/u/74838

## 对 GBT 的启示
- 可吸收点: 结合仓库定位与 README 技术栈, 提炼可注入 GBT cap 的知识

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
