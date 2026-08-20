package org.opensearch.guardian;

import org.opensearch.action.ActionType;
import org.opensearch.core.action.ActionResponse;
import org.opensearch.plugins.ActionPlugin;
import org.opensearch.plugins.Plugin;
import org.opensearch.guardian.action.GuardianStartCollectionAction;
import org.opensearch.guardian.action.GuardianStopCollectionAction;
import org.opensearch.guardian.action.GuardianGetStatusAction;

import java.util.List;

/**
 * Main plugin entry point for OpenSearch Guardian.
 * Implements ActionPlugin SPI interface.
 */
public class GuardianPlugin extends Plugin implements ActionPlugin {

    @Override
    public List<org.opensearch.plugins.ActionPlugin.ActionHandler<?, ?>> getActions() {
        return List.of();
    }

    @Override
    public List<ActionType<? extends ActionResponse>> getClientActions() {
        return List.of(
            GuardianStartCollectionAction.INSTANCE,
            GuardianStopCollectionAction.INSTANCE,
            GuardianGetStatusAction.INSTANCE
        );
    }
}
