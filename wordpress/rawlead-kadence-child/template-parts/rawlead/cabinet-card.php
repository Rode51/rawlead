<?php
/**
 * Cabinet inbox card delta (O127 §9.2e) — render in rawlead-cabinet.js accordion.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

/**
 * Cabinet cards use the same .rl-lead-card shell; tier is always premium in inbox context.
 */
function rawlead_cabinet_card_tier(): string {
    return 'premium';
}
