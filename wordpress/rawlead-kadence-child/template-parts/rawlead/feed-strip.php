<?php
/**
 * Feed strip — O116 Z2: anon / free / paid (paid hidden via JS after /v1/me).
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$cabinet_login = esc_url(rawlead_cabinet_login_url());
$pricing = esc_url(rawlead_page_url('pricing'));
?>
<div class="rl-feed-strip" id="rl-feed-strip" hidden>
	<div class="rl-feed-strip__anon">
		<span class="rl-feed-strip__text"><?php esc_html_e('⏱ Лента с задержкой 15 мин ·', 'rawlead-kadence-child'); ?></span>
		<a class="rl-feed-strip__cta" href="<?php echo $cabinet_login; ?>"><?php esc_html_e('Войди — сразу →', 'rawlead-kadence-child'); ?></a>
	</div>
	<div class="rl-feed-strip__free">
		<span class="rl-feed-strip__text"><span class="rl-feed-strip__ok" aria-hidden="true">✅</span> <?php esc_html_e('Лента без задержки ·', 'rawlead-kadence-child'); ?></span>
		<a class="rl-feed-strip__cta" href="<?php echo $pricing; ?>"><?php esc_html_e('Черновики — Premium →', 'rawlead-kadence-child'); ?></a>
	</div>
</div>
