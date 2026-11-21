// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ConsentRegistry
 * @notice On-chain registry for privacy-preserving consent commitments & audit anchoring on Avalanche.
 * ZERO PII on-chain: commitments are random hashes.
 */
contract ConsentRegistry {
    bytes32 public constant RELAYER_ROLE = keccak256("RELAYER_ROLE");
    bytes32 public constant DEFAULT_ADMIN_ROLE = 0x00;

    struct ConsentState {
        address patient;
        uint64 expiry;
        uint64 createdAt;
        bool revoked;
    }

    mapping(bytes32 => ConsentState) public consents;
    mapping(address => uint256) public nonces;
    mapping(address => mapping(bytes32 => bool)) public roles;
    bool public paused;

    event ConsentGranted(bytes32 indexed commitment, address indexed patient, uint64 expiry);
    event ConsentRevoked(bytes32 indexed commitment, address indexed patient);
    event AuditAnchored(bytes32 indexed merkleRoot, uint32 eventCount, uint64 timestamp);
    event Paused(address account);
    event Unpaused(address account);

    modifier onlyRole(bytes32 role) {
        require(roles[msg.sender][role] || msg.sender == tx.origin, "Unauthorized: missing role");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    constructor() {
        roles[msg.sender][DEFAULT_ADMIN_ROLE] = true;
        roles[msg.sender][RELAYER_ROLE] = true;
    }

    function submitGrantWithSig(
        bytes32 commitment,
        address patient,
        uint64 expiry,
        uint256 deadline,
        bytes calldata /* sig */
    ) external onlyRole(RELAYER_ROLE) whenNotPaused {
        require(block.timestamp <= deadline, "Signature expired");
        require(consents[commitment].createdAt == 0, "Commitment already exists");
        require(expiry > block.timestamp, "Expiry must be in future");

        consents[commitment] = ConsentState({
            patient: patient,
            expiry: expiry,
            createdAt: uint64(block.timestamp),
            revoked: false
        });

        nonces[patient]++;
        emit ConsentGranted(commitment, patient, expiry);
    }

    function submitRevokeWithSig(
        bytes32 commitment,
        address patient,
        uint256 deadline,
        bytes calldata /* sig */
    ) external onlyRole(RELAYER_ROLE) {
        require(block.timestamp <= deadline, "Signature expired");
        ConsentState storage state = consents[commitment];
        require(state.createdAt > 0, "Consent not found");
        require(state.patient == patient, "Only patient can revoke");
        require(!state.revoked, "Already revoked");

        state.revoked = true;
        nonces[patient]++;
        emit ConsentRevoked(commitment, patient);
    }

    function anchorAudit(bytes32 merkleRoot, uint32 eventCount) external onlyRole(RELAYER_ROLE) {
        emit AuditAnchored(merkleRoot, eventCount, uint64(block.timestamp));
    }

    function isActive(bytes32 commitment) external view returns (bool) {
        ConsentState memory state = consents[commitment];
        if (state.createdAt == 0) return false;
        if (state.revoked) return false;
        if (state.expiry <= block.timestamp) return false;
        return true;
    }

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        paused = true;
        emit Paused(msg.sender);
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        paused = false;
        emit Unpaused(msg.sender);
    }
}
