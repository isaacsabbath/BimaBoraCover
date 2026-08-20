// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title BimaRegistry
/// @notice On-chain proof-of-existence registry for Bima Afya policy issuance
///         and claim payouts. Ported from BimaOS (CodeWithEugene/BimaOS) for
///         deployment on Polygon Amoy testnet. Not a source of truth for
///         business state — Postgres remains authoritative. This contract only
///         anchors immutable hashes/events so a policy or payout can be proven
///         to have existed at a given block time.
contract BimaRegistry {
    address public owner;

    struct Policy {
        bytes32 id;
        address user;
        uint256 premiumAmount;
        uint256 coverageAmount;
        string policyType;
        uint256 timestamp;
        bool active;
    }

    struct Claim {
        bytes32 id;
        bytes32 policyId;
        address user;
        uint256 payoutAmount;
        string status;
        uint256 timestamp;
        bool exists;
    }

    mapping(bytes32 => Policy) public policies;
    mapping(bytes32 => Claim) public claims;

    event PolicyRegistered(bytes32 indexed policyId, address indexed user, uint256 premium, uint256 coverage, string policyType);
    event ClaimPayoutRegistered(bytes32 indexed claimId, bytes32 indexed policyId, address indexed user, uint256 payoutAmount, string status);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function registerPolicy(
        bytes32 _policyId,
        address _user,
        uint256 _premium,
        uint256 _coverage,
        string memory _policyType
    ) external onlyOwner {
        require(policies[_policyId].id == bytes32(0), "Policy already registered");

        policies[_policyId] = Policy({
            id: _policyId,
            user: _user,
            premiumAmount: _premium,
            coverageAmount: _coverage,
            policyType: _policyType,
            timestamp: block.timestamp,
            active: true
        });

        emit PolicyRegistered(_policyId, _user, _premium, _coverage, _policyType);
    }

    function registerClaimPayout(
        bytes32 _claimId,
        bytes32 _policyId,
        address _user,
        uint256 _payoutAmount,
        string memory _status
    ) external onlyOwner {
        require(claims[_claimId].id == bytes32(0), "Claim already registered");

        claims[_claimId] = Claim({
            id: _claimId,
            policyId: _policyId,
            user: _user,
            payoutAmount: _payoutAmount,
            status: _status,
            timestamp: block.timestamp,
            exists: true
        });

        emit ClaimPayoutRegistered(_claimId, _policyId, _user, _payoutAmount, _status);
    }

    function verifyClaim(bytes32 _claimId) external view returns (bool exists, string memory status, uint256 payoutAmount) {
        Claim memory c = claims[_claimId];
        return (c.exists, c.status, c.payoutAmount);
    }
}
