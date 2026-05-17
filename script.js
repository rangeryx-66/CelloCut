const resultSets = {
  celloscan: {
    ids: [
      30, 40, 42, 35,
      18, 22, 24, 31,
      32, 33, 36, 39,
      41, 44, 46, 47,
      48, 132, 8, 26,
    ],
    inputDir: "assets/videos/celloscan/input",
    outputDir: "assets/videos/celloscan/output",
  },
  cellofill: {
    ids: [
      0, 1, 2, 4,
      8, 9, 12, 13,
      14, 15, 17, 18,
      22, 24, 28, 29,
      30, 31, 32, 33,
      37, 39, 40, 42,
    ],
    inputDir: "assets/videos/cellofill/input",
    outputDir: "assets/videos/cellofill/output",
  },
};

const resultsPerPage = 4;

const makeVideo = (src, label) => {
  const figure = document.createElement("figure");
  figure.className = "comparison-video";

  const video = document.createElement("video");
  video.src = src;
  video.autoplay = true;
  video.loop = true;
  video.muted = true;
  video.playsInline = true;
  video.preload = "metadata";
  video.setAttribute("aria-label", label);

  const caption = document.createElement("figcaption");
  caption.textContent = label;

  figure.append(video, caption);
  return figure;
};

const renderResultPage = (browser, config, pageIndex) => {
  const grid = browser.querySelector("[data-result-grid]");
  const pager = browser.querySelector(".result-pager");
  if (!grid || !pager) return;

  const start = pageIndex * resultsPerPage;
  const pageIds = config.ids.slice(start, start + resultsPerPage);
  grid.replaceChildren();

  pageIds.forEach((id, offset) => {
    const card = document.createElement("article");
    card.className = "comparison-card";

    const title = document.createElement("h4");
    title.textContent = `Example ${start + offset + 1}`;

    const media = document.createElement("div");
    media.className = "comparison-media";
    media.append(
      makeVideo(`${config.inputDir}/${id}.mp4`, "Input"),
      makeVideo(`${config.outputDir}/${id}.mp4`, "CelloCut"),
    );

    card.append(title, media);
    grid.append(card);
  });

  [...pager.querySelectorAll("button")].forEach((button, index) => {
    const isCurrent = index === pageIndex;
    button.classList.toggle("is-active", isCurrent);
    button.setAttribute("aria-current", isCurrent ? "page" : "false");
  });
};

document.querySelectorAll("[data-result-browser]").forEach((browser) => {
  const key = browser.dataset.resultBrowser;
  const config = resultSets[key];
  const pager = browser.querySelector(".result-pager");
  if (!config || !pager) return;

  const pageCount = Math.ceil(config.ids.length / resultsPerPage);

  for (let pageIndex = 0; pageIndex < pageCount; pageIndex += 1) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = String(pageIndex + 1);
    button.addEventListener("click", () => renderResultPage(browser, config, pageIndex));
    pager.append(button);
  }

  renderResultPage(browser, config, 0);
});
