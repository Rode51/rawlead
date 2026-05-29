<?php
/**
 * Sticky header — REFERENCE §3.1 · WAVE-4-ADDON
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$home = home_url('/');
$feed = rawlead_page_url('lenta');
$cabinet = rawlead_page_url('cabinet');
$is_app = function_exists('rawlead_is_app_page') && rawlead_is_app_page();
$is_cabinet = is_page('cabinet');
$mark_svg = RAWLEAD_CHILD_DIR . '/assets/images/wave2-mark-radar-v1.svg';

$current = '';
if (!is_front_page() && is_page()) {
    $post = get_queried_object();
    if ($post instanceof WP_Post) {
        $current = $post->post_name;
    }
}

$nav = [
    'lenta'   => [__('Лента', 'rawlead-kadence-child'), $feed],
    'pricing' => [__('Тарифы', 'rawlead-kadence-child'), rawlead_page_url('pricing')],
    'how'     => [__('Как устроено', 'rawlead-kadence-child'), rawlead_page_url('how')],
];
?>
<?php if (is_front_page()) : ?>
<div class="rl-announcement" role="region" aria-label="<?php esc_attr_e('Объявление', 'rawlead-kadence-child'); ?>">
	<div class="rl-container rl-announcement__inner">
		<p class="rl-announcement__text">
			<span class="rl-announcement__text-full"><?php esc_html_e('Радар онлайн · 800+ лидов в неделю ·', 'rawlead-kadence-child'); ?></span>
			<span class="rl-announcement__text-short"><?php esc_html_e('800+ лидов', 'rawlead-kadence-child'); ?></span>
		</p>
		<a class="rl-announcement__cta" href="<?php echo esc_url($feed); ?>">
			<span class="rl-announcement__cta-full"><?php esc_html_e('Смотреть ленту →', 'rawlead-kadence-child'); ?></span>
			<span class="rl-announcement__cta-short"><?php esc_html_e('Смотреть →', 'rawlead-kadence-child'); ?></span>
		</a>
	</div>
</div>
<?php endif; ?>
<header class="rl-header<?php echo $is_app ? ' rl-header--minimal' : ''; ?>" role="banner">
	<div class="rl-container rl-header__inner">
		<a href="<?php echo esc_url($home); ?>" class="rl-logo" aria-label="<?php esc_attr_e('RawLead — на главную', 'rawlead-kadence-child'); ?>">
			<span class="rl-logo__icon" aria-hidden="true">
				<?php if (is_readable($mark_svg)) : ?>
					<?php // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- inline SVG asset
					echo file_get_contents($mark_svg); ?>
				<?php endif; ?>
			</span>
			<span class="rl-logo__text-block">
				<span class="rl-logo__name">RawLead</span>
				<?php if (!$is_app) : ?>
					<span class="rl-logo__by">by Rode51</span>
				<?php endif; ?>
			</span>
		</a>
		<nav aria-label="<?php esc_attr_e('Основное меню', 'rawlead-kadence-child'); ?>">
			<ul class="rl-header__nav">
				<?php foreach ($nav as $slug => $item) : ?>
					<?php $active = $current === $slug ? ' is-active' : ''; ?>
					<li>
						<a class="rl-header__link<?php echo esc_attr($active); ?>" href="<?php echo esc_url($item[1]); ?>">
							<?php echo esc_html($item[0]); ?>
						</a>
					</li>
				<?php endforeach; ?>
			</ul>
		</nav>
		<div class="rl-header__cta">
			<?php if ($is_cabinet) : ?>
				<a href="<?php echo esc_url($feed); ?>" class="rl-header__back"><?php esc_html_e('← Лента', 'rawlead-kadence-child'); ?></a>
			<?php else : ?>
				<a href="<?php echo esc_url($cabinet); ?>" class="rl-header__login js-header-login"><?php esc_html_e('Войти →', 'rawlead-kadence-child'); ?></a>
				<a href="<?php echo esc_url($cabinet); ?>" class="rl-header__user js-header-user" hidden>
					<img class="rl-header__avatar js-header-avatar" src="" alt="" width="32" height="32">
					<span class="rl-header__username js-header-username"></span>
				</a>
			<?php endif; ?>
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
		var loginEl = document.querySelector(".js-header-login");
		var userEl = document.querySelector(".js-header-user");
		if (!loginEl || !userEl) {
			return;
		}
		var avatarEl = document.querySelector(".js-header-avatar");
		var nameEl = document.querySelector(".js-header-username");
		var token = "";
		try {
			token = localStorage.getItem(TOKEN_KEY) || "";
		} catch (e) {
			token = "";
		}
		if (!token) {
			loginEl.hidden = false;
			userEl.hidden = true;
			if (avatarEl) {
				avatarEl.removeAttribute("src");
			}
			return;
		}
		loginEl.hidden = true;
		userEl.hidden = false;
		var meta = readMeta();
		if (meta && meta.photo_url && avatarEl) {
			avatarEl.src = meta.photo_url;
		} else if (avatarEl) {
			avatarEl.removeAttribute("src");
		}
		if (nameEl && meta) {
			var username = (meta.username || "").trim();
			nameEl.textContent = username ? "@" + username : meta.display || "Telegram";
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
