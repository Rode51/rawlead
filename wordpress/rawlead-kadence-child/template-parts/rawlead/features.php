<?php
/**
 * Features 01 · 02 · 03 — REFERENCE §3.5
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$items = [
    [
        'title' => __('Один поток', 'rawlead-kadence-child'),
        'text'  => __('Биржи, агрегаторы, Telegram-каналы — всё в одной ленте. Не нужно переключаться между вкладками и чатами.', 'rawlead-kadence-child'),
    ],
    [
        'title' => __('ИИ читает суть заказа', 'rawlead-kadence-child'),
        'text'  => __('Система понимает задачу и сверяет с твоим стеком — не по ключевым словам, а по смыслу.', 'rawlead-kadence-child'),
    ],
    [
        'title' => __('Уникальный отклик', 'rawlead-kadence-child'),
        'text'  => __('Каждый получает свою формулировку — ИИ адаптирует текст под тебя. На бирже не выглядишь как бот — не один шаблон на всех. Пишешь и отправляешь сам — мы не спамим за тебя.', 'rawlead-kadence-child'),
    ],
];

$trust_chips = [
    __('Не один текст на всех', 'rawlead-kadence-child'),
    __('Не автоспам', 'rawlead-kadence-child'),
    __('Не бан за шаблон', 'rawlead-kadence-child'),
];
?>
<section class="rl-section rl-features-scroll rl-reveal" aria-labelledby="rl-features-title">
	<div class="rl-container">
		<div class="rl-features-scroll__head">
			<h2 id="rl-features-title"><?php esc_html_e('Один поток вместо десяти вкладок', 'rawlead-kadence-child'); ?></h2>
		</div>
		<div class="rl-features-track">
			<?php foreach ($items as $item) : ?>
				<article class="rl-feature">
					<h3 class="rl-feature__title"><?php echo esc_html($item['title']); ?></h3>
					<p class="rl-feature__text"><?php echo esc_html($item['text']); ?></p>
				</article>
			<?php endforeach; ?>
		</div>
		<div class="rl-trust-strip" aria-label="<?php esc_attr_e('Почему RawLead безопасен', 'rawlead-kadence-child'); ?>">
			<div class="rl-trust-strip__chips">
				<?php foreach ($trust_chips as $chip) : ?>
					<span class="rl-trust-strip__chip"><?php echo esc_html($chip); ?></span>
				<?php endforeach; ?>
			</div>
			<p class="rl-trust-strip__mobile"><?php esc_html_e('Свой черновик у каждого', 'rawlead-kadence-child'); ?></p>
		</div>
	</div>
</section>
