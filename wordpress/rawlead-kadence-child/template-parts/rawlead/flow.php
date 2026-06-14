<?php
/**
 * Flow block — O81-w1 animated illustration (Design § O81-w1).
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$mark_svg = RAWLEAD_CHILD_DIR . '/assets/images/wave2-mark-radar-v1.svg';
$home     = home_url('/');
?>
<section class="rl-flow rl-flow-anim rl-section" aria-labelledby="rl-flow-title">
	<div class="rl-container">
		<h2 id="rl-flow-title" class="rl-flow__title"><?php esc_html_e('Один поток вместо десяти вкладок', 'rawlead-kadence-child'); ?></h2>

		<div class="rl-flow-anim__inner">
			<div class="rl-flow-anim__stage">
				<div class="rl-flow-anim__logo-wrap" id="rl-flow-logo">
					<div class="rl-flow-logo__scale">
						<div class="rl-flow-logo__shake">
							<div class="rl-flow-logo__reaction">
								<a href="<?php echo esc_url($home); ?>" class="rl-logo rl-flow-anim__logo" aria-label="<?php esc_attr_e('RawLead — на главную', 'rawlead-kadence-child'); ?>">
									<span class="rl-logo__icon" aria-hidden="true">
										<?php if (is_readable($mark_svg)) : ?>
											<?php // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- inline SVG asset
											echo file_get_contents($mark_svg); ?>
										<?php endif; ?>
									</span>
									<span class="rl-logo__text-block">
										<span class="rl-logo__name">RawLead</span>
										<span class="rl-logo__by">by Rode51</span>
									</span>
								</a>
							</div>
						</div>
					</div>
				</div>

				<div class="rl-flow-anim__chips" aria-hidden="true">
					<div class="rl-flow-chip" data-source="fl" data-dx="-440" data-dy="5" data-ms="0" data-color="#00A65A" data-rot="5deg">
						<span class="rl-flow-chip__dot" style="background:#00A65A"></span>FL.ru
					</div>
					<div class="rl-flow-chip" data-source="kwork" data-dx="465" data-dy="-55" data-ms="210" data-color="#EA580C" data-rot="-8deg">
						<span class="rl-flow-chip__dot" style="background:#EA580C"></span>Kwork
					</div>
					<div class="rl-flow-chip" data-source="tg" data-dx="15" data-dy="-292" data-ms="420" data-color="#0088CC" data-rot="3deg">
						<span class="rl-flow-chip__dot" style="background:#0088CC"></span>Telegram
					</div>
					<div class="rl-flow-chip" data-source="youdo" data-dx="-385" data-dy="228" data-ms="630" data-color="#2563EB" data-rot="-5deg">
						<span class="rl-flow-chip__dot" style="background:#2563EB"></span>YouDo
					</div>
					<div class="rl-flow-chip" data-source="freelance_ru" data-dx="455" data-dy="215" data-ms="840" data-color="#7C3AED" data-rot="7deg">
						<span class="rl-flow-chip__dot" style="background:#7C3AED"></span>Freelance.ru
					</div>
				</div>

				<div class="rl-flow-anim__ripples" aria-hidden="true"></div>
			</div>

			<div class="rl-flow-anim__cards" aria-hidden="true">
				<article class="rl-lead-card rl-flow-anim__card rl-flow-anim__card--perfect" data-match="87">
					<div class="rl-feed-card__head">
						<div class="rl-feed-card__head-start">
							<span class="rl-feed-card__source rl-feed-card__source--fl">FL.ru</span>
							<span class="rl-badge rl-badge--perfect">ИДЕАЛЬНО ✦</span>
						</div>
					</div>
					<h3 class="rl-lead-card__title"><?php esc_html_e('Telegram-бот для автоматизации заявок', 'rawlead-kadence-child'); ?></h3>
					<p class="rl-lead-card__budget"><?php esc_html_e('Бюджет: 25 000 ₽', 'rawlead-kadence-child'); ?></p>
					<div class="rl-match">
						<div class="rl-match__label"><span><?php esc_html_e('Совместимость 87%', 'rawlead-kadence-child'); ?></span></div>
						<div class="rl-match__bar" role="progressbar" aria-valuenow="87" aria-valuemin="0" aria-valuemax="100">
							<span class="rl-match__fill" style="--match-value:0%"></span>
						</div>
					</div>
				</article>

				<article class="rl-lead-card rl-flow-anim__card" data-match="73">
					<div class="rl-feed-card__head">
						<div class="rl-feed-card__head-start">
							<span class="rl-feed-card__source rl-feed-card__source--kwork">Kwork</span>
						</div>
					</div>
					<h3 class="rl-lead-card__title"><?php esc_html_e('Парсер маркетплейсов на Python', 'rawlead-kadence-child'); ?></h3>
					<p class="rl-lead-card__budget"><?php esc_html_e('Бюджет: 15 000 ₽', 'rawlead-kadence-child'); ?></p>
					<div class="rl-match">
						<div class="rl-match__label"><span><?php esc_html_e('Совместимость 73%', 'rawlead-kadence-child'); ?></span></div>
						<div class="rl-match__bar" role="progressbar" aria-valuenow="73" aria-valuemin="0" aria-valuemax="100">
							<span class="rl-match__fill" style="--match-value:0%"></span>
						</div>
					</div>
				</article>

				<article class="rl-lead-card rl-flow-anim__card" data-match="61">
					<div class="rl-feed-card__head">
						<div class="rl-feed-card__head-start">
							<span class="rl-feed-card__source rl-feed-card__source--tg">Telegram</span>
						</div>
					</div>
					<h3 class="rl-lead-card__title"><?php esc_html_e('Лендинг для SaaS-продукта на WP', 'rawlead-kadence-child'); ?></h3>
					<p class="rl-lead-card__budget"><?php esc_html_e('Бюджет: 40 000 ₽', 'rawlead-kadence-child'); ?></p>
					<div class="rl-match">
						<div class="rl-match__label"><span><?php esc_html_e('Совместимость 61%', 'rawlead-kadence-child'); ?></span></div>
						<div class="rl-match__bar" role="progressbar" aria-valuenow="61" aria-valuemin="0" aria-valuemax="100">
							<span class="rl-match__fill" style="--match-value:0%"></span>
						</div>
					</div>
				</article>
			</div>
		</div>

		<p class="rl-flow__caption"><?php esc_html_e('Меньше вкладок, больше откликов.', 'rawlead-kadence-child'); ?></p>
	</div>
</section>
