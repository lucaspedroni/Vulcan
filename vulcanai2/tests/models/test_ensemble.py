import pytest
import numpy as np
import torch
from vulcanai2.models.cnn import ConvNet
from vulcanai2.models.dnn import DenseNet
from vulcanai2.models.ensemble import SnapshotNet
from torch.utils.data import TensorDataset, DataLoader


class TestSnapshotNet:
    """Test SnapshotNet functionality."""

    @pytest.fixture
    def cnn_noclass(self):
        """Create intermediate conv module."""
        return ConvNet(
            name='Test_ConvNet_noclass',
            dimensions=(1, 28, 28),
            config={
                'conv_units': [
                    {
                        "in_channels": 1,
                        "out_channels": 16,
                        "kernel_size": (5, 5),
                        "stride": 2
                    },
                    {
                        "in_channels": 16,
                        "out_channels": 1,
                        "kernel_size": (5, 5),
                        "stride": 1,
                        "padding": 2
                    }]
            }
        )

    @pytest.fixture
    def dnn_class(self, cnn_noclass):
        """Create dnn module prediction leaf node."""
        return DenseNet(
            name='Test_DenseNet_class',
            input_network=cnn_noclass,
            dimensions=cnn_noclass.conv_flat_dim,
            config={
                'dense_units': [100, 50],
                'initializer': None,
                'bias_init': None,
                'norm': None,
                'dropout': 0.5,  # Single value or List
            },
            num_classes=3
        )

    def test_snapshot_structure(self, cnn_noclass, dnn_class):
        """Confirm Snapshot structure is generated properly."""
        test_input = torch.ones([1, *cnn_noclass.in_dim]).float()
        test_target = torch.ones([1]).long()
        test_dataloader = DataLoader(TensorDataset(test_input, test_target))
        test_snap = SnapshotNet(
            name='test_snap',
            template_network=dnn_class,
            n_snapshots=3
        )
        test_snap.fit(
            train_loader=test_dataloader,
            val_loader=test_dataloader,
            epochs=3,
            plot=False
        )
        assert test_snap.template_network.lr_scheduler is not None
        # Check correct number of generated snapshots
        assert len(test_snap.snapshot_networks.keys()) == 3
        # Check snapshots are not identical
        assert list(test_snap.snapshot_networks.values())[0] is not \
            list(test_snap.snapshot_networks.values())[1] is not \
            list(test_snap.snapshot_networks.values())[2]
        output = test_snap.forward_pass(
            data_loader=test_dataloader,
            convert_to_class=False)
        assert np.any(~np.isnan(output))
