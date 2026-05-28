<?php
/**
 * Sticky header — REFERENCE §3.1
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$home = home_url('/');
$feed = rawlead_page_url('lenta');

$current = '';
if (!is_front_page() && is_page()) {
    $post = get_queried_object();
    if ($post instanceof WP_Post) {
        $current = $post->post_name;
    }
}

$cabinet = rawlead_page_url('cabinet');

$nav = [
    'lenta'   => [__('Лента', 'rawlead-kadence-child'), $feed],
    'pricing' => [__('Тарифы', 'rawlead-kadence-child'), rawlead_page_url('pricing')],
];
?>
<header class="rl-header" role="banner">
	<div class="rl-container rl-header__inner">
		<a class="rl-header__brand" href="<?php echo esc_url($home); ?>">RawLead</a>
		<nav aria-label="<?php esc_attr_e('Основное меню', 'rawlead-kadence-child'); ?>">
			<ul class="rl-header__nav">
				<?php foreach ($nav as $slug => $item) : ?>
					<?php
					$active = $current === $slug ? ' is-active' : '';
					?>
					<li>
						<a class="rl-header__link<?php echo esc_attr($active); ?>" href="<?php echo esc_url($item[1]); ?>">
							<?php echo esc_html($item[0]); ?>
						</a>
					</li>
				<?php endforeach; ?>
			</ul>
		</nav>
		<div class="rl-header__cta">
			<a class="rl-btn rl-btn--primary rl-header__cta-link" href="<?php echo esc_url($cabinet); ?>" id="rl-header-cta">
				<img class="rl-header__avatar" id="rl-header-avatar" alt="" width="28" height="28" hidden>
				<span id="rl-header-cta-text"><?php esc_html_e('Вход в ЛК', 'rawlead-kadence-child'); ?></span>
			</a>
		</div>
	</div>
</header>
<script>
(function () {
	var TOKEN_KEY = "rawlead_access_token";
	var META_KEY = "rawlead_user_meta";

	function readMeta() {
		try {
			var raw = localStorage.getItem(META_KEY);
			if (!raw) {
				return null;
			}
			return JSON.parse(raw);
		} catch (e) {
			return null;
		}
	}

	window.rawleadSyncHeader = function () {
		var el = document.getElementById("rl-header-cta");
		var textEl = document.getElementById("rl-header-cta-text");
		var avatarEl = document.getElementById("rl-header-avatar");
		if (!el || !textEl) {
			return;
		}
		var token = "";
		try {
			token = localStorage.getItem(TOKEN_KEY) || "";
		} catch (e) {
			token = "";
		}
		if (!token) {
			textEl.textContent = "Вход в ЛК";
			el.classList.remove("rl-header__cta-link--logged-in");
			if (avatarEl) {
				avatarEl.hidden = true;
				avatarEl.removeAttribute("src");
			}
			return;
		}
		textEl.textContent = "Кабинет";
		el.classList.add("rl-header__cta-link--logged-in");
		var meta = readMeta();
		if (avatarEl && meta && meta.photo_url) {
			avatarEl.src = meta.photo_url;
			avatarEl.hidden = false;
		} else if (avatarEl) {
			avatarEl.hidden = true;
			avatarEl.removeAttribute("src");
		}
	};

	window.rawleadSyncHeader();
	window.addEventListener("rawlead-auth-changed", window.rawleadSyncHeader);
	window.addEventListener("storage", function (e) {
		if (e.key === TOKEN_KEY || e.key === META_KEY) {
			window.rawleadSyncHeader();
		}
	});
})();
</script>
