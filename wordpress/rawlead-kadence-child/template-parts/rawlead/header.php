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
			<a class="rl-btn rl-btn--primary" href="<?php echo esc_url($cabinet); ?>" id="rl-header-cta">
				<?php esc_html_e('Вход в ЛК', 'rawlead-kadence-child'); ?>
			</a>
		</div>
	</div>
</header>
<script>
(function () {
	var key = "rawlead_access_token";
	var el = document.getElementById("rl-header-cta");
	if (!el) {
		return;
	}
	try {
		if (localStorage.getItem(key)) {
			el.textContent = "Кабинет";
		}
	} catch (e) {
		/* private mode */
	}
})();
</script>
