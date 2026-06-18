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
<?php $quiz = esc_url(rawlead_quiz_url()); ?>
<div class="rl-feed-strip" id="rl-feed-strip" hidden>
	<div class="rl-feed-strip__anon rl-feed-anon-strip">
		<span class="rl-feed-anon-strip__delay"><?php esc_html_e('Заказы с задержкой 30 мин.', 'rawlead-kadence-child'); ?></span>
		<a class="rl-feed-anon-strip__cta" href="<?php echo $quiz; ?>"><?php esc_html_e('Войди через TG — 3 дня Premium бесплатно', 'rawlead-kadence-child'); ?></a>
	</div>
	<div class="rl-feed-strip__free">
		<span class="rl-feed-strip__text"><span class="rl-feed-strip__ok" aria-hidden="true">✅</span> <?php esc_html_e('Лента без задержки ·', 'rawlead-kadence-child'); ?></span>
		<a class="rl-feed-strip__cta" href="<?php echo $pricing; ?>"><?php esc_html_e('Черновики — Premium →', 'rawlead-kadence-child'); ?></a>
	</div>
</div>
