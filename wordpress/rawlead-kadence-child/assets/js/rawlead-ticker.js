/**
 * Home announcement ticker — O116 M3 (3 phrases · 27s · pause hover · live stats).
 */
(function () {
	var root = document.querySelector("[data-rl-ticker]");
	if (!root) {
		return;
	}

	var slides = Array.prototype.slice.call(
		root.querySelectorAll("[data-rl-ticker-slide]")
	);
	if (slides.length < 2) {
		return;
	}

	var cycleMs = 27000;
	var index = 0;
	var timer = null;

	function showSlide(i) {
		slides.forEach(function (slide, idx) {
			var on = idx === i;
			slide.classList.toggle("is-active", on);
			slide.hidden = !on;
		});
	}

	function nextSlide() {
		index = (index + 1) % slides.length;
		showSlide(index);
	}

	function startTimer() {
		if (timer) {
			clearInterval(timer);
		}
		timer = setInterval(nextSlide, cycleMs);
	}

	function pauseTimer() {
		if (timer) {
			clearInterval(timer);
			timer = null;
		}
	}

	root.addEventListener("mouseenter", function () {
		root.classList.add("is-paused");
		pauseTimer();
	});
	root.addEventListener("mouseleave", function () {
		root.classList.remove("is-paused");
		startTimer();
	});
	root.addEventListener("focusin", pauseTimer);
	root.addEventListener("focusout", function (e) {
		if (!root.contains(e.relatedTarget)) {
			startTimer();
		}
	});

	showSlide(0);
	startTimer();

	var weekEls = root.querySelectorAll("[data-rl-leads-week], [data-rl-leads-week-short]");
	var statsUrl =
		(typeof rawleadTicker !== "undefined" && rawleadTicker.restStats) ||
		"/wp-json/rawlead/v1/site-stats";

	function formatLeadsWeek(n) {
		var num = Math.max(0, parseInt(String(n), 10) || 0);
		if (num < 10) {
			return String(num);
		}
		var bucket = Math.floor(num / 10) * 10;
		return String(bucket) + "+";
	}

	function applyLeadsWeek(label) {
		weekEls.forEach(function (el) {
			if (el.hasAttribute("data-rl-leads-week-short")) {
				el.textContent = label;
			} else {
				el.textContent = label;
			}
		});
	}

	fetch(statsUrl, { credentials: "same-origin" })
		.then(function (res) {
			if (!res.ok) {
				throw new Error("stats http " + res.status);
			}
			return res.json();
		})
		.then(function (data) {
			var n =
				data && typeof data.leads_week_display === "number"
					? data.leads_week_display
					: data && typeof data.leads_week === "number"
						? data.leads_week
						: 0;
			applyLeadsWeek(formatLeadsWeek(n));
		})
		.catch(function () {
			applyLeadsWeek("…");
		});
})();
