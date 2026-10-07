/* tick-779: ASCII box-art fits instead of wrapping. tick-760's pre-wrap
   keeps long code lines readable, but it destroys box-drawing diagrams
   (┌─┐ comparison tables, tier charts): lines break mid-word and the
   frame mixes with the text - the corpus carries 287 such blocks across
   84 pages. For each art-like block: measure the longest line, shrink
   the monospace font just enough to fit the container (floor 9px);
   beyond the floor, scroll horizontally with the art intact. Non-art
   code blocks keep tick-760's wrapping. Purely visual, content files
   untouched. */
(function () {
  var BOX = /[─│┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬]/;
  var FRAME = /^\s*[+|][-+=|]*[+|]\s*$/;

  function isAsciiArt(text) {
    var lines = text.split("\n");
    var boxLines = 0, frameLines = 0;
    for (var i = 0; i < lines.length; i++) {
      if (BOX.test(lines[i])) boxLines++;
      if (FRAME.test(lines[i])) frameLines++;
    }
    return boxLines >= 2 || frameLines >= 3;
  }

  function fit(pre) {
    var code = pre.querySelector("code");
    if (!code) return;
    // reset any previous fitting first so the measurement is clean
    code.style.whiteSpace = "";
    code.style.fontSize = "";
    pre.style.overflowX = "";
    pre.classList.remove("ascii-fit");
    if (!isAsciiArt(code.textContent)) return;

    pre.classList.add("ascii-fit");
    code.style.whiteSpace = "pre"; // keep newlines and columns intact
    pre.style.overflowX = "hidden";
    var base = parseFloat(getComputedStyle(code).fontSize);
    // pre.scrollWidth under-reports here: the block-level code child keeps
    // its overflowing inline line boxes out of the parent's scroll area, so
    // a 619px-wide box art measures 485px and clips invisibly.
    // code.scrollWidth is the honest signal for the unwrapped line extent.
    var contentW = code.scrollWidth;
    var avail = pre.clientWidth;
    if (contentW - avail <= 1) return; // already fits at the current size
    var size = Math.floor((base * avail) / contentW);
    if (size >= 9) {
      code.style.fontSize = size + "px";
    } else {
      code.style.fontSize = "9px"; // floor: scroll the rest, art intact
      pre.style.overflowX = "auto";
    }
  }

  function run() {
    document.querySelectorAll(".md-typeset pre").forEach(fit);
  }

  if (window.document$) {
    document$.subscribe(run); // re-fits on Material's instant navigation
  } else {
    document.addEventListener("DOMContentLoaded", run);
  }
  var t;
  window.addEventListener("resize", function () {
    clearTimeout(t);
    t = setTimeout(run, 150);
  });
})();
